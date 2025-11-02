# Privacy-Preserving Architecture for slop.at

**Date:** October 30, 2025  
**Status:** Design Document  
**Context:** Federated knowledge sharing with privacy by default

## Core Principle

**Privacy by Default, Sharing by Choice**

Users maintain full control over their data through a dual-database architecture:
- **Local Oxigraph:** Private knowledge base on user's machine
- **Remote Oxigraph:** Public/shared knowledge on federated servers

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User's Machine                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │         Local Oxigraph Database              │      │
│  │         (~/.slop/oxigraph/local.db)         │      │
│  ├──────────────────────────────────────────────┤      │
│  │  • Private slops                             │      │
│  │  • Drafts                                    │      │
│  │  • Personal notes                            │      │
│  │  • Work-in-progress                          │      │
│  │  • Sensitive content                         │      │
│  └──────────────────────────────────────────────┘      │
│                         ↕                                │
│  ┌──────────────────────────────────────────────┐      │
│  │         Sync Agent / Federation Layer        │      │
│  ├──────────────────────────────────────────────┤      │
│  │  • Selective publishing                      │      │
│  │  • Friend subscriptions                      │      │
│  │  • Query routing                             │      │
│  │  • Privacy level enforcement                 │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ↕
                    Internet
                          ↕
┌─────────────────────────────────────────────────────────┐
│              Remote Federated Servers                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────┐      │
│  │      Public Oxigraph Database                │      │
│  │      (slop.at or personal server)            │      │
│  ├──────────────────────────────────────────────┤      │
│  │  • Published slops                           │      │
│  │  • Shared concepts                           │      │
│  │  • Attribution chains                        │      │
│  │  • Cross-references                          │      │
│  │  • Community knowledge                       │      │
│  └──────────────────────────────────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Privacy Levels

### 1. Local (Private)
**Never leaves your machine**

```turtle
@prefix slop: <http://slop.at/ontology/> .

<slop:rob/private_idea_123> a slop:Slop ;
    slop:privacy "local" ;
    slop:author "rob" ;
    slop:content "Sensitive company strategy notes..." ;
    slop:published false .
```

- Stored only in local Oxigraph
- Not discoverable by others
- Not synced to any remote server
- Full semantic search locally

### 2. Friends Only
**Federated to trusted connections**

```turtle
<slop:rob/friend_only_456> a slop:Slop ;
    slop:privacy "friends" ;
    slop:author "rob" ;
    slop:content "Working on a new feature for Pixeltable..." ;
    slop:published true ;
    slop:visibleTo ( <user:alice> <user:bob> ) .
```

- Synced to friends' local Oxigraph
- Not visible on public servers
- Peer-to-peer sharing model
- Maintains attribution chains

### 3. Public
**Open to the world**

```turtle
<slop:rob/public_789> a slop:Slop ;
    slop:privacy "public" ;
    slop:author "rob" ;
    slop:content "My thoughts on semantic web architecture..." ;
    slop:published true ;
    slop:publishedTo <server:slop.at> .
```

- Synced to public remote servers
- Discoverable via search
- Part of global knowledge graph
- Full federation support

## Data Flow

### Publishing Flow

```
User creates slop
       ↓
Saved to Local Oxigraph (always)
       ↓
User selects privacy level
       ↓
    [Decision]
       ↓
   ┌───┴────┬──────────┐
   ↓        ↓          ↓
Local    Friends    Public
(done)      ↓          ↓
       Encrypt &  Push to
       sync to    remote
       friends    server
```

### Query Flow

```
User searches for concepts
         ↓
    Query Router
         ↓
   ┌─────┴─────┐
   ↓           ↓
Local      Remote
Query      Query
   ↓           ↓
Results   Results
   ↓           ↓
   └─────┬─────┘
         ↓
   Merge & Rank
         ↓
    Display
  (clearly labeled
   local vs remote)
```

## Implementation Details

### Local Oxigraph Setup

```python
class LocalOxigraph:
    def __init__(self, user_home: Path):
        self.db_path = user_home / ".slop" / "oxigraph" / "local.db"
        self.store = Store(str(self.db_path))
    
    def add_slop(self, slop: Slop, privacy: Privacy = Privacy.LOCAL):
        """Add slop to local database with privacy metadata"""
        triples = [
            (slop.uri, RDF.type, SLOP.Slop),
            (slop.uri, SLOP.privacy, Literal(privacy.value)),
            (slop.uri, SLOP.author, Literal(slop.author)),
            (slop.uri, SLOP.content, Literal(slop.content)),
            (slop.uri, SLOP.created, Literal(datetime.now())),
        ]
        
        for triple in triples:
            self.store.add(triple)
        
        # Extract concepts and add semantic triples
        concepts = extract_concepts(slop.content)
        for concept in concepts:
            self.store.add((slop.uri, SLOP.discusses, concept.uri))
    
    def query_local(self, sparql: str) -> List[Dict]:
        """Query only local database"""
        return list(self.store.query(sparql))
```

### Sync Agent

```python
class SyncAgent:
    def __init__(self, local_store: LocalOxigraph, remote_servers: List[str]):
        self.local = local_store
        self.remotes = remote_servers
        self.friends = self.load_friend_list()
    
    def publish_slop(self, slop_uri: URIRef, privacy: Privacy):
        """Publish slop based on privacy level"""
        if privacy == Privacy.LOCAL:
            # Nothing to sync
            return
        
        if privacy == Privacy.FRIENDS:
            # Encrypt and send to friends
            self.sync_to_friends(slop_uri)
        
        if privacy == Privacy.PUBLIC:
            # Push to remote servers
            self.push_to_remote(slop_uri)
    
    def sync_to_friends(self, slop_uri: URIRef):
        """Peer-to-peer encrypted sync"""
        slop_data = self.local.get_slop(slop_uri)
        
        for friend in self.friends:
            encrypted_data = encrypt_for_friend(slop_data, friend.public_key)
            send_to_peer(friend.endpoint, encrypted_data)
    
    def push_to_remote(self, slop_uri: URIRef):
        """Push to public remote servers"""
        slop_data = self.local.get_slop(slop_uri)
        
        for server in self.remotes:
            response = requests.post(
                f"{server}/api/slops",
                json=slop_data,
                headers={"Authorization": f"Bearer {self.get_token(server)}"}
            )
            
            if response.ok:
                # Store remote URI mapping
                self.local.add_remote_mapping(slop_uri, response.json()["remote_uri"])
```

### Federated Query Router

```python
class QueryRouter:
    def __init__(self, local: LocalOxigraph, remotes: List[str]):
        self.local = local
        self.remotes = remotes
    
    def search(self, query: str, include_remote: bool = True) -> SearchResults:
        """Route queries to local and optionally remote stores"""
        
        # Always search local first
        local_results = self.local.semantic_search(query)
        
        if not include_remote:
            return SearchResults(
                local=local_results,
                remote=[],
                total=len(local_results)
            )
        
        # Federated search across remote servers
        remote_results = []
        for server in self.remotes:
            try:
                results = self.query_remote_server(server, query)
                remote_results.extend(results)
            except Exception as e:
                logger.warning(f"Failed to query {server}: {e}")
        
        # Merge and rank
        merged = self.merge_and_rank(local_results, remote_results)
        
        return SearchResults(
            local=local_results,
            remote=remote_results,
            merged=merged,
            total=len(merged)
        )
    
    def query_remote_server(self, server: str, query: str) -> List[Slop]:
        """Query a remote server"""
        response = requests.post(
            f"{server}/api/search",
            json={"query": query, "limit": 20}
        )
        return [Slop.from_json(r) for r in response.json()["results"]]
```

## User Experience

### Creating a Slop

```
┌──────────────────────────────────────────┐
│  New Slop                                │
├──────────────────────────────────────────┤
│                                          │
│  Title: [My thoughts on RDF]            │
│                                          │
│  Content:                                │
│  ┌────────────────────────────────────┐ │
│  │ RDF provides a flexible way to     │ │
│  │ model knowledge...                 │ │
│  └────────────────────────────────────┘ │
│                                          │
│  Privacy:                                │
│  ○ Private (just me)                     │
│  ○ Friends only                          │
│  ● Public (discoverable)                 │
│                                          │
│  Tags: [semantic-web] [rdf] [knowledge] │
│                                          │
│  [Cancel]              [Save & Publish] │
└──────────────────────────────────────────┘
```

### Search Results

```
┌──────────────────────────────────────────┐
│  Search: "semantic web architecture"    │
├──────────────────────────────────────────┤
│                                          │
│  📍 Local Results (3)                    │
│  ┌────────────────────────────────────┐ │
│  │ 🔒 My notes on RDF design          │ │
│  │    Private • 2 days ago             │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ 👥 Discussion with Alice           │ │
│  │    Friends • 1 week ago             │ │
│  └────────────────────────────────────┘ │
│                                          │
│  🌐 Public Results (12)                 │
│  ┌────────────────────────────────────┐ │
│  │ Semantic Web Best Practices        │ │
│  │    @tim_berners_lee • 3 days ago    │ │
│  │    🌐 slop.at                        │ │
│  └────────────────────────────────────┘ │
│                                          │
│  [Load more public results...]          │
└──────────────────────────────────────────┘
```

## GitHub Integration

### Private Repos (Local Slops)
```
user-repos/
└── rob/
    └── private-slops/          # Private GitHub repo
        ├── thoughts/
        │   └── 2025-10-30-semantic-web.md
        ├── drafts/
        │   └── work-in-progress.md
        └── .slop/
            └── metadata.ttl    # RDF metadata, .gitignored
```

### Public Repos (Published Slops)
```
slop-repos/
└── rob/
    └── public-slops/           # Public GitHub repo
        ├── technology/
        │   └── 2025-10-30-rdf-architecture.md
        ├── philosophy/
        │   └── 2025-10-25-knowledge-graphs.md
        └── .slop/
            ├── concepts.ttl    # Extracted concepts
            └── metadata.ttl    # Publication metadata
```

## Federation Protocol

### Server Discovery

```json
{
  "server": "slop.at",
  "version": "0.1.0",
  "capabilities": [
    "semantic_search",
    "concept_extraction",
    "friend_federation",
    "sparql_endpoint"
  ],
  "endpoints": {
    "publish": "https://slop.at/api/slops",
    "search": "https://slop.at/api/search",
    "sparql": "https://slop.at/sparql",
    "federation": "https://slop.at/api/federation"
  },
  "privacy_levels": ["public", "friends", "unlisted"],
  "ontologies": [
    "http://slop.at/ontology/core",
    "http://schema.org/",
    "http://xmlns.com/foaf/0.1/"
  ]
}
```

### Friend Federation

```json
{
  "action": "share_slop",
  "from": "rob@slop.local",
  "to": "alice@slop.local",
  "slop": {
    "uri": "slop:rob/friend_only_456",
    "encrypted_content": "...",
    "signature": "...",
    "metadata": {
      "created": "2025-10-30T10:00:00Z",
      "concepts": ["semantic-web", "privacy"],
      "references": []
    }
  }
}
```

## Security Considerations

### Encryption
- **Local Database:** Optional full-disk encryption
- **Friend Sharing:** End-to-end encryption using public keys
- **Remote Sync:** TLS for transport, optional content encryption

### Authentication
- **Local:** User's machine, no auth needed
- **Remote Servers:** OAuth2 / API keys
- **Federation:** Mutual TLS, signed requests

### Data Integrity
- **Git History:** Immutable version control
- **Cryptographic Signatures:** Verify authorship
- **Hash-based URIs:** Content-addressable references

## Migration & Export

### Export Your Data
```bash
# Export all local slops
slop export --format turtle --output my-knowledge-graph.ttl

# Export to different formats
slop export --format json-ld --output my-slops.jsonld
slop export --format markdown --output slops-archive/

# Clone your GitHub repos
git clone https://github.com/rob/private-slops
git clone https://github.com/rob/public-slops
```

### Import to New Server
```bash
# Import from another slop instance
slop import --from ~/.old-slop/oxigraph/

# Import from GitHub
slop import --github rob/public-slops

# Import from RDF file
slop import --turtle my-knowledge-graph.ttl
```

## Benefits

### For Users
✅ **Privacy Control:** You decide what to share  
✅ **Data Ownership:** Your data stays yours  
✅ **Portability:** Export and migrate anytime  
✅ **Offline First:** Full functionality without internet  
✅ **Selective Sharing:** Friends-only or public options  

### For Developers
✅ **Clear Separation:** Local vs remote logic  
✅ **Federation Ready:** Built for distributed networks  
✅ **Git Integration:** Familiar version control  
✅ **Standard Protocols:** RDF, SPARQL, REST APIs  

### For the Network
✅ **Decentralized:** No single point of failure  
✅ **Scalable:** Each user maintains their data  
✅ **Privacy-Preserving:** Opt-in sharing model  
✅ **Interoperable:** Standard semantic web formats  

## Implementation Roadmap

### Phase 1: Local-Only (v0.0.1)
- [x] Local Oxigraph setup
- [ ] Basic slop creation
- [ ] Semantic search locally
- [ ] Privacy metadata

### Phase 2: GitHub Sync (v0.0.2)
- [ ] Sync to GitHub repos (private/public)
- [ ] Git-based versioning
- [ ] Import from GitHub

### Phase 3: Friend Federation (v0.1.0)
- [ ] Friend connection protocol
- [ ] Encrypted peer-to-peer sharing
- [ ] Friend discovery

### Phase 4: Public Federation (v0.2.0)
- [ ] Remote server sync
- [ ] Federated search
- [ ] Cross-server attribution
- [ ] Server discovery protocol

## Open Questions

1. **Encryption Standard:** What encryption for friend sharing? (Age, GPG, libsodium?)
2. **Discovery Mechanism:** How do users find other servers? (DNS-based? Centralized registry?)
3. **Conflict Resolution:** What happens if same slop edited locally and remotely?
4. **Storage Limits:** Should local database have size limits?
5. **Sync Frequency:** Real-time, periodic, or manual sync to remotes?

## Related Documents
- [Core Architecture](./2025_10_30_SLOPAT_V0_ARCHITECTURE.md)
- [Distributed Slop](./2025_10_30_DISTRIBUTED_SLOP_FEDERATED_KNOWLEDGE.md)

---

**Next Steps:**
1. Implement basic local Oxigraph
2. Add privacy level metadata to slop schema
3. Build simple sync agent
4. Test with GitHub private repos
5. Design friend federation protocol
