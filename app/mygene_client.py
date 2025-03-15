import requests
import time
import functools
from app.logger import get_logger

logger = get_logger()


@functools.lru_cache(maxsize=100)
def search_gene_by_symbol(symbol, timeout=5):
    """Search for a gene by its symbol using MyGene.info API with caching."""
    url = f"https://mygene.info/v3/query?q=symbol:{symbol}&species=human"

    try:
        logger.info(f"Searching for gene {symbol} via MyGene.info API (first search or cache miss)")
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if data.get('hits') and len(data['hits']) > 0:
            gene_id = data['hits'][0].get('_id', 'unknown')
            logger.info(f"Found gene {symbol} with ID {gene_id}")
            return data['hits'][0]
        else:
            logger.warning(f"No results found for gene {symbol}")
            return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while searching for gene {symbol}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error searching for gene {symbol}: {e}")
        return None


@functools.lru_cache(maxsize=200)
def get_publication_details(pmid, timeout=3):
    """Get publication details from PubMed API with caching."""
    try:
        logger.info(f"Fetching details for publication {pmid} (first fetch or cache miss)")
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if 'result' in data and pmid in data['result']:
            pub_data = data['result'][pmid]
            pub_date = pub_data.get('pubdate', "Unknown")
            title = pub_data.get('title', f"Publication {pmid}")

            # Get citation count
            citations = 0
            try:
                cite_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id={pmid}&linkname=pubmed_pubmed_citedin&retmode=json"
                cite_response = requests.get(cite_url, timeout=timeout)
                cite_data = cite_response.json()

                if 'linksets' in cite_data and len(cite_data['linksets']) > 0:
                    linkset = cite_data['linksets'][0]
                    if 'linksetdbs' in linkset and len(linkset['linksetdbs']) > 0:
                        citations = len(linkset['linksetdbs'][0].get('links', []))
                        logger.info(f"Publication {pmid} has {citations} citations")
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.warning(f"Error getting citation count for PMID {pmid}: {e}")

            return {
                'pmid': pmid,
                'title': title,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
                'date': pub_date,
                'citations': citations
            }

        logger.warning(f"Publication data not found for PMID {pmid}")
        return {
            'pmid': pmid,
            'title': f"Publication {pmid}",
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
            'date': "Unknown",
            'citations': 0
        }
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching details for PMID {pmid}")
        return {
            'pmid': pmid,
            'title': f"Publication {pmid} (details unavailable)",
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
            'date': "Unknown",
            'citations': 0
        }
    except Exception as e:
        logger.error(f"Error fetching details for PMID {pmid}: {e}")
        return {
            'pmid': pmid,
            'title': f"Publication {pmid} (error retrieving details)",
            'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}",
            'date': "Unknown",
            'citations': 0
        }


@functools.lru_cache(maxsize=50)
def get_gene_publications(gene_id, timeout=15, max_papers=50):
    """Get scientific publications related to a gene by its ID with caching."""
    url = f"https://mygene.info/v3/gene/{gene_id}"

    try:
        logger.info(f"Fetching publications for gene ID {gene_id} (first fetch or cache miss)")
        start_time = time.time()

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        pmids = set()  # To avoid duplicates

        # Check for publications in generif field
        if 'generif' in data:
            for pub in data['generif']:
                if 'pubmed' in pub:
                    pmids.add(str(pub['pubmed']))

        # Check for publications in reporter field
        if 'reporter' in data and 'publications' in data['reporter']:
            for pmid in data['reporter']['publications']:
                pmids.add(str(pmid))

        logger.info(f"Found {len(pmids)} PMIDs for gene ID {gene_id}")

        # Limit the number of PMIDs to process
        pmids_list = list(pmids)[:max_papers]

        # Get details for each publication
        publications = []
        for pmid in pmids_list:
            if time.time() - start_time > timeout - 2:  # Reserve 2 seconds
                logger.warning(f"Timeout limit approaching, stopping at {len(publications)} papers")
                break

            pub_details = get_publication_details(pmid)
            if pub_details:
                publications.append(pub_details)

        logger.info(f"Retrieved details for {len(publications)} publications for gene ID {gene_id}")
        return publications
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching publications for gene ID {gene_id}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching publications for gene ID {gene_id}: {e}")
        return []


# Not caching this function as it often gets called with different timeout/max_papers parameters
def get_papers_for_gene(gene_symbol, max_papers=50, timeout=20):
    """Get scientific papers related to a gene symbol."""
    logger.info(f"Starting paper search for gene {gene_symbol} (max: {max_papers}, timeout: {timeout}s)")
    start_time = time.time()

    # Search for gene ID
    gene_info = search_gene_by_symbol(gene_symbol, timeout=5)
    if not gene_info or '_id' not in gene_info:
        logger.warning(f"No gene ID found for symbol {gene_symbol}")
        return []

    # Get publications using gene ID
    elapsed = time.time() - start_time
    remaining_timeout = max(1, timeout - elapsed)
    gene_id = gene_info['_id']
    logger.info(f"Found gene ID {gene_id}, fetching papers with {remaining_timeout:.1f}s timeout")

    # For consistent caching, use fixed values if the remaining time is sufficient
    if remaining_timeout >= 15:
        papers = get_gene_publications(gene_id, timeout=15, max_papers=max_papers)
    else:
        # If time is limited, pass the actual remaining timeout
        papers = get_gene_publications(gene_id, timeout=remaining_timeout, max_papers=max_papers)

    logger.info(f"Completed paper search for {gene_symbol}: found {len(papers)} papers in {time.time() - start_time:.2f}s")
    return papers