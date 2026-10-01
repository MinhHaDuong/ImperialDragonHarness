# Corpus Analysis Methods Reference

Detailed guide to computational methods for validating and illustrating findings from critical literature reviews.

## General Principles

**Purpose:** Computational methods COMPLEMENT qualitative analysis, they don't replace it.

**Use cases:**
- Confirm patterns identified qualitatively
- Illustrate structures more clearly (visualizations)
- Discover unexpected patterns for investigation
- Provide quantitative validation for interpretive claims

**Not a replacement for:**
- Close reading and interpretation
- Theoretical analysis
- Understanding historical context
- Identifying silent controversies

## Method 1: Vectorization and Clustering

### Purpose
- Identify thematic groups automatically
- Validate that identified "coalitions" cluster together
- Discover potential groupings not identified qualitatively

### When to Use
- Corpus of 50+ documents
- Want to validate actor coalitions
- Exploring thematic structure

### Implementation

**Libraries:** sentence-transformers, scikit-learn, umap-learn

```python
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
import umap

# 1. Load texts (abstracts or full text)
texts = [doc['abstract'] for doc in corpus]

# 2. Create embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, good quality
embeddings = model.encode(texts, show_progress_bar=True)

# 3. Reduce dimensions for visualization
reducer = umap.UMAP(n_neighbors=15, min_dist=0.1, metric='cosine')
embedding_2d = reducer.fit_transform(embeddings)

# 4. Cluster
n_clusters = 5  # Choose based on domain knowledge
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(embeddings)

# 5. Analyze clusters
for i in range(n_clusters):
    cluster_docs = [doc for doc, c in zip(corpus, clusters) if c == i]
    print(f"Cluster {i}: {len(cluster_docs)} documents")
    # Examine: Are OECD docs together? Civil society separate?
```

### Validation Questions
- Do documents from same institution cluster together?
- Do identified "coalitions" form distinct clusters?
- Are there unexpected clusters? (investigate qualitatively)
- Do clusters align with analytical axes?

### Output for Technical Report
- 2D scatter plot with clusters colored
- Cluster membership table
- Interpretation: "Cluster 1 (N=23) consists primarily of OECD methodological documents..."

## Method 2: Topic Modeling

### Purpose
- Discover latent topics across corpus
- Track topic evolution over time
- Validate theoretical tensions identified qualitatively

### When to Use
- Corpus of 100+ documents
- Want to discover thematic structure
- Interested in temporal evolution

### Implementation

**Library:** BERTopic (state-of-the-art, coherent topics)

```python
from bertopic import BERTopic
import pandas as pd

# 1. Prepare data
texts = [doc['abstract'] + " " + doc['title'] for doc in corpus]
timestamps = [doc['year'] for doc in corpus]

# 2. Fit topic model
topic_model = BERTopic(
    language="english",
    calculate_probabilities=True,
    verbose=True
)

topics, probs = topic_model.fit_transform(texts)

# 3. Examine topics
topic_info = topic_model.get_topic_info()
print(topic_info)  # Shows top words per topic

# 4. Analyze over time
topics_over_time = topic_model.topics_over_time(
    texts, 
    timestamps,
    nr_bins=10  # Divide period into 10 time bins
)

# 5. Topic distribution by institution
df = pd.DataFrame({
    'topic': topics,
    'institution': [doc['institution_type'] for doc in corpus]
})
topic_by_inst = df.groupby(['institution', 'topic']).size().unstack(fill_value=0)
```

### Validation Questions
- Do discovered topics align with identified controversies?
- Are efficiency-focused topics distinct from justice-focused?
- How do topics evolve over time?
- Do institutions specialize in certain topics?

### Output for Technical Report
- Top words for each topic (table)
- Topic prevalence over time (line plot)
- Topic distribution by institution (heatmap)
- Interpretation connecting topics to theoretical frameworks

## Method 3: Citation Network Analysis

### Purpose
- Map intellectual influence patterns
- Identify central works and peripheral
- Detect communities (groups of mutually-citing works)

### When to Use
- Corpus with citation data available
- Want to visualize influence structure
- Identifying seminal vs derivative works

### Implementation

**Library:** NetworkX

```python
import networkx as nx

# 1. Build citation graph
G = nx.DiGraph()

# Add nodes (documents)
for doc in corpus:
    G.add_node(doc['id'], title=doc['title'], year=doc['year'])

# Add edges (citations)
for doc in corpus:
    citing_id = doc['id']
    for cited_id in doc['citations']:  # Extracted from PDFs
        if cited_id in [d['id'] for d in corpus]:  # Within-corpus citation
            G.add_edge(citing_id, cited_id)

# 2. Calculate centrality
degree_cent = nx.degree_centrality(G)
betweenness = nx.betweenness_centrality(G)
pagerank = nx.pagerank(G)

# 3. Detect communities
communities = nx.community.louvain_communities(G.to_undirected())

# 4. Identify central works
top_cited = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]

# 5. Analyze communities
for i, community in enumerate(communities):
    docs_in_comm = [doc for doc in corpus if doc['id'] in community]
    print(f"Community {i}: {len(docs_in_comm)} documents")
    # Check institutional composition
```

### Validation Questions
- Do identified coalitions form distinct communities?
- Are bridge documents connecting different perspectives?
- Which works are most central within each community?
- Do citation patterns reveal intellectual genealogies?

### Output for Technical Report
- Network visualization with communities colored
- Table of most central works
- Community composition analysis
- Interpretation: "Network analysis reveals three distinct communities..."

## Method 4: Keyword and Concept Evolution

### Purpose
- Track when concepts emerge and stabilize
- Show concept frequency over time
- Identify co-occurring concepts

### When to Use
- Want to validate periodization
- Tracking specific terminology
- Showing concept emergence

### Implementation

**Libraries:** pandas, nltk, keybert

```python
import pandas as pd
from collections import Counter
import re

# 1. Extract keywords by year
keywords_of_interest = ['additionality', 'mobilization', 'climate finance', 'leverage']

keyword_counts = []
for year in sorted(set(doc['year'] for doc in corpus)):
    year_docs = [doc for doc in corpus if doc['year'] == year]
    year_text = " ".join([doc['abstract'] for doc in year_docs]).lower()
    
    counts = {kw: len(re.findall(r'\b' + kw + r'\b', year_text)) 
              for kw in keywords_of_interest}
    counts['year'] = year
    keyword_counts.append(counts)

df_keywords = pd.DataFrame(keyword_counts)

# 2. Co-occurrence analysis
from itertools import combinations

cooccur = Counter()
for doc in corpus:
    text_lower = (doc['abstract'] + " " + doc['title']).lower()
    present_keywords = [kw for kw in keywords_of_interest if kw in text_lower]
    for pair in combinations(present_keywords, 2):
        cooccur[pair] += 1

# 3. Automated keyword extraction (for discovery)
from keybert import KeyBERT

kw_model = KeyBERT()
all_text = " ".join([doc['abstract'] for doc in corpus])
keywords_auto = kw_model.extract_keywords(
    all_text, 
    keyphrase_ngram_range=(1, 3),
    top_n=20
)
```

### Validation Questions
- When do key concepts first appear?
- Which concepts co-occur frequently?
- Does keyword evolution match historical periodization?
- Are there temporal clusters of concept introduction?

### Output for Technical Report
- Timeline showing keyword frequency
- Co-occurrence network
- Table of concept first appearances
- Interpretation: "The term 'additionality' emerges in 1997..."

## Method 5: Temporal Analysis

### Purpose
- Characterize different time periods
- Show field evolution
- Validate historical periodization

### When to Use
- Corpus spans multiple years/decades
- Want to show how field evolved
- Testing periodization hypotheses

### Implementation

```python
import pandas as pd
import matplotlib.pyplot as plt

# 1. Divide corpus into periods
periods = {
    '1990-2000': 'Category formation',
    '2001-2010': 'Methodology development', 
    '2011-2020': 'Measurement controversies',
    '2021-2025': 'Consolidation and critique'
}

# 2. Analyze each period
for period_range, period_name in periods.items():
    start, end = map(int, period_range.split('-'))
    period_docs = [doc for doc in corpus if start <= doc['year'] <= end]
    
    # Count by institution type
    inst_counts = Counter(doc['institution_type'] for doc in period_docs)
    
    # Average citations
    avg_citations = sum(doc['citation_count'] for doc in period_docs) / len(period_docs)
    
    # Dominant topics (if topic modeling done)
    period_topics = [doc['topic'] for doc in period_docs]
    topic_dist = Counter(period_topics)
    
    print(f"{period_name} ({period_range}): {len(period_docs)} docs")
    print(f"  Top institution: {inst_counts.most_common(1)}")
    print(f"  Dominant topic: {topic_dist.most_common(1)}")

# 3. Publication trends
pub_by_year = Counter(doc['year'] for doc in corpus)
df_pubs = pd.DataFrame(list(pub_by_year.items()), columns=['Year', 'Count'])
df_pubs.plot(x='Year', y='Count', kind='line')
```

### Validation Questions
- Do computational periods match qualitative periodization?
- How does institutional composition change over time?
- When do controversies emerge in publication patterns?
- Are there acceleration points in publication activity?

### Output for Technical Report
- Publication timeline by actor type
- Period comparison table
- Topic evolution visualization
- Interpretation: "Three distinct periods are evident..."

## Method 6: Controversy Detection

### Purpose
- Identify documents representing opposing positions
- Validate controversy structure
- Discover unidentified controversies

### When to Use
- Want quantitative validation of controversies
- Exploring potential new controversies
- Showing polarization

### Implementation

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# 1. For documents discussing same topic, compare positions
# Example: All docs mentioning "additionality"

additionality_docs = [doc for doc in corpus if 'additionality' in doc['abstract'].lower()]

# 2. Vectorize these documents
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode([doc['abstract'] for doc in additionality_docs])

# 3. Find most dissimilar pairs (likely opposing positions)
sim_matrix = cosine_similarity(embeddings)
n = len(additionality_docs)

dissimilar_pairs = []
for i in range(n):
    for j in range(i+1, n):
        dissimilar_pairs.append((i, j, sim_matrix[i][j]))

# Lowest similarity = most opposing
dissimilar_pairs.sort(key=lambda x: x[2])
most_opposed = dissimilar_pairs[:5]

# 4. Analyze language differences
# Compare word frequencies between "poles"
pole_1_docs = additionality_docs[:len(additionality_docs)//2]  # Top half by some criterion
pole_2_docs = additionality_docs[len(additionality_docs)//2:]

# Distinctive words for each pole
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(max_features=50)
pole_1_text = " ".join([doc['abstract'] for doc in pole_1_docs])
pole_2_text = " ".join([doc['abstract'] for doc in pole_2_docs])

tfidf_matrix = vectorizer.fit_transform([pole_1_text, pole_2_text])
feature_names = vectorizer.get_feature_names_out()

# Top distinctive words
pole_1_distinctive = sorted(zip(feature_names, tfidf_matrix[0].toarray()[0]), 
                            key=lambda x: x[1], reverse=True)[:10]
pole_2_distinctive = sorted(zip(feature_names, tfidf_matrix[1].toarray()[0]), 
                            key=lambda x: x[1], reverse=True)[:10]
```

### Validation Questions
- Do identified controversy sides show linguistic differences?
- Are there multiple distinct positions (not just binary)?
- Do computational methods reveal controversies missed qualitatively?
- How polarized are the debates?

### Output for Technical Report
- Pairs of documents representing opposing positions
- Distinctive vocabulary for each side
- Similarity distribution (histogram)
- Interpretation: "Quantitative analysis confirms polarization..."

## Integration Guidelines

### How to Present Computational Findings

**DO:**
- Present as complementary to qualitative analysis
- Interpret in theoretical context
- Acknowledge limitations
- Connect to specific claims from qualitative work

**DON'T:**
- Present as definitive proof
- Use jargon without explanation
- Rely solely on computational findings
- Ignore contradictions with qualitative analysis

### Typical Figure/Table Set

**Recommended for Technical Report (3-6 total):**

1. **Corpus overview** (table or figure)
   - Distribution by year, institution, category
   
2. **Thematic structure** (visualization)
   - Cluster plot OR topic prevalence
   
3. **Network structure** (if citation data available)
   - Communities with key nodes labeled
   
4. **Temporal evolution** (timeline)
   - Publication trends OR concept evolution
   
5. **Controversy validation** (optional)
   - Dissimilarity scores OR distinctive vocabulary

6. **Validation summary** (table)
   - Qualitative finding | Computational confirmation | Method used

### Workflow Summary

1. **Consult with user** before heavy analysis
2. **Prepare corpus** (aggregate files, extract text)
3. **Create corpus analysis table** with annotations
4. **Select methods** based on research questions
5. **Run analysis** with careful parameter choices
6. **Interpret results** in theoretical context
7. **Create figures/tables** for technical report
8. **Write corpus analysis report** documenting all steps
9. **Integrate findings** into technical report (Step 7)

## Common Pitfalls

**Avoid:**
- Running all methods on autopilot
- Using default parameters without understanding
- Over-interpreting small effects
- Ignoring outliers or anomalies
- Presenting results without qualitative context

**Instead:**
- Choose methods purposefully
- Understand and document parameter choices
- Report effect sizes and confidence
- Investigate anomalies qualitatively
- Always connect computational to interpretive findings

## Further Resources

**Python Libraries:**
- sentence-transformers: https://www.sbert.net/
- BERTopic: https://maartengr.github.io/BERTopic/
- NetworkX: https://networkx.org/
- scikit-learn: https://scikit-learn.org/

**Tutorials:**
- Text clustering: https://github.com/cjhutto/vaderSentiment <!-- harness-extension-point -->
- Topic modeling: BERTopic documentation
- Network analysis: NetworkX tutorials

**Academic References:**
- Bail, C. A. (2014). The cultural environment: Measuring culture with big data. Theory and Society.
- DiMaggio, P., et al. (2013). Exploiting affinities between topic modeling and the sociological perspective on culture. Poetics.
- Mohr, J. W., & Bogdanov, P. (2013). Introduction—Topic models: What they are and why they matter. Poetics.
