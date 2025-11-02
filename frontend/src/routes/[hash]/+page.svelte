<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';

	// Get hash from route params
	$: hash = $page.params.hash;

	let slopData = null;
	let loading = true;
	let error = null;
	let selectedConcept = null;
	let sidebarOpen = true;

	// Fetch slop data on component mount
	onMount(async () => {
		try {
			const response = await fetch(`/api/slops/${hash}`);
			if (!response.ok) {
				throw new Error(`Failed to load slop: ${response.statusText}`);
			}
			slopData = await response.json();
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	});

	// Handle concept click
	async function handleConceptClick(conceptText, domain, linkId) {
		selectedConcept = { text: conceptText, domain, linkId, relatedSlops: null, loading: true };

		// Fetch related slops from the API
		try {
			const response = await fetch(`/api/concepts/${encodeURIComponent(conceptText)}/slops`);
			const data = await response.json();
			selectedConcept = { ...selectedConcept, relatedSlops: data.related_slops, loading: false };
		} catch (err) {
			console.error('Failed to fetch related slops:', err);
			selectedConcept = { ...selectedConcept, loading: false, error: err.message };
		}
	}

	// Toggle sidebar
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}
</script>

{#if slopData}
	<div class="page-actions">
		<button on:click={() => window.location.href = `/${hash}/edit`}>Edit</button>
		<button on:click={toggleSidebar}>
			{sidebarOpen ? 'Hide' : 'Show'} Concepts
		</button>
	</div>
{/if}

<div class="slop-view">
	{#if loading}
		<div class="loading">Loading...</div>
	{:else if error}
		<div class="error">Error: {error}</div>
	{:else if slopData}
		<div class="main-content">
			<article>
				{@html slopData.html}
			</article>
		</div>

		{#if sidebarOpen}
			<aside class="sidebar">
				<h2>Concepts</h2>

				{#if selectedConcept}
					<div class="selected-concept">
						<h3>{selectedConcept.text}</h3>
						<p class="domain">{selectedConcept.domain}</p>
						<div class="related-slops">
							<h4>Related Slops</h4>
							{#if selectedConcept.loading}
								<p class="loading-text">Loading...</p>
							{:else if selectedConcept.error}
								<p class="error-text">Error: {selectedConcept.error}</p>
							{:else if selectedConcept.relatedSlops && selectedConcept.relatedSlops.length > 0}
								<ul class="related-list">
									{#each selectedConcept.relatedSlops as relatedSlop}
										<li>
											<a href={relatedSlop.url}>{relatedSlop.title}</a>
										</li>
									{/each}
								</ul>
							{:else}
								<p class="no-results">No related slops found (yet!)</p>
							{/if}
						</div>
					</div>
				{:else}
					<p class="hint">Click a highlighted concept to see related slops</p>
				{/if}

				<div class="all-concepts">
					<h4>All Concepts ({slopData.concepts?.length || 0})</h4>
					<ul>
						{#each slopData.concepts || [] as concept}
							<li class="concept-{concept.domain}">
								<button on:click={() => handleConceptClick(concept.text, concept.domain, concept.linkId)}>
									{concept.text}
								</button>
								<span class="confidence">{(concept.confidence * 100).toFixed(0)}%</span>
							</li>
						{/each}
					</ul>
				</div>
			</aside>
		{/if}
	{/if}
</div>

<style>
	.slop-view {
		display: flex;
		min-height: calc(100vh - 180px);
		max-width: 1600px;
		margin: 0 auto;
	}

	.loading, .error {
		margin: 2rem;
		padding: 1.5rem;
		border-radius: 8px;
		border: 1px solid var(--color-border);
	}

	.loading {
		background: var(--color-bg-secondary);
		color: var(--color-text-secondary);
	}

	.error {
		background: rgba(220, 38, 38, 0.1);
		border-color: rgba(220, 38, 38, 0.3);
		color: #fca5a5;
	}

	.main-content {
		flex: 1;
		padding: 4rem 6rem;
		max-width: 900px;
		min-width: 0;
		margin: 0 auto;
	}

	button {
		padding: 0.625rem 1.25rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		background: var(--color-bg-secondary);
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	button:hover {
		background: var(--color-teal-dark);
		border-color: var(--color-teal);
		color: var(--color-cyan);
		box-shadow: 0 0 12px var(--color-glow-cyan);
	}

	article {
		line-height: 1.8;
		font-size: 1.125rem;
		font-family: var(--font-serif);
		color: var(--color-text-primary);
	}

	article :global(h1) {
		font-family: var(--font-body);
		font-size: 2.5rem;
		margin-top: 0;
		margin-bottom: 0.75em;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--color-blue);
	}

	article :global(p) {
		margin-bottom: 1.5em;
		line-height: 1.8;
		color: var(--color-text-primary);
	}

	article :global(h2) {
		font-family: var(--font-body);
		margin-top: 2.5em;
		margin-bottom: 0.75em;
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--color-blue);
	}

	article :global(h3) {
		font-family: var(--font-body);
		margin-top: 2em;
		margin-bottom: 0.5em;
		font-size: 1.375rem;
		font-weight: 700;
		color: var(--color-blue-bright);
	}

	article :global(blockquote) {
		border-left: 3px solid var(--color-teal-bright);
		padding-left: 1.5rem;
		margin-left: 0;
		margin-right: 0;
		font-style: italic;
		color: var(--color-text-secondary);
	}

	article :global(ul), article :global(ol) {
		margin-bottom: 1.5em;
		padding-left: 2rem;
	}

	article :global(li) {
		margin-bottom: 0.5em;
	}

	article :global(code) {
		background: var(--color-bg-secondary);
		padding: 0.2em 0.4em;
		border-radius: 3px;
		font-size: 0.9em;
		color: var(--color-text-secondary);
		font-family: var(--font-mono);
	}

	article :global(pre) {
		background: var(--color-bg-secondary);
		padding: 1rem;
		border-radius: 6px;
		overflow-x: auto;
		border: 1px solid var(--color-border);
	}

	article :global(pre code) {
		background: none;
		padding: 0;
		color: var(--color-text-primary);
	}

	article :global(a) {
		color: var(--color-blue);
		text-decoration: none;
		transition: color 0.2s ease;
	}

	article :global(a:hover) {
		color: var(--color-blue-bright);
	}

	.sidebar {
		width: 320px;
		padding: 2rem 1.5rem;
		background: var(--color-bg-secondary);
		border-left: 1px solid var(--color-border);
		overflow-y: auto;
	}

	.sidebar h2 {
		font-family: var(--font-sans);
		font-size: 1rem;
		margin-bottom: 1.5rem;
		color: var(--color-text-primary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 600;
	}

	.hint {
		color: var(--color-text-dim);
		font-style: italic;
		font-size: 0.9375rem;
	}

	.selected-concept {
		background: var(--color-bg-tertiary);
		padding: 1.25rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
		border: 1px solid var(--color-border);
	}

	.selected-concept h3 {
		font-size: 1.125rem;
		margin-bottom: 0.5rem;
		color: var(--color-blue);
	}

	.domain {
		color: var(--color-text-dim);
		font-size: 0.8125rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 600;
	}

	.related-slops h4 {
		font-size: 0.9375rem;
		margin: 1rem 0 0.75rem;
		color: var(--color-text-secondary);
	}

	.all-concepts h4 {
		font-size: 0.9375rem;
		margin-bottom: 0.75rem;
		color: var(--color-text-secondary);
	}

	.all-concepts ul {
		list-style: none;
		padding: 0;
	}

	.all-concepts li {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.625rem;
		margin: 0.375rem 0;
		background: var(--color-bg-tertiary);
		border-radius: 6px;
		border: 1px solid transparent;
		transition: all 0.2s ease;
	}

	.all-concepts li:hover {
		border-color: var(--color-teal);
		background: var(--color-teal-dark);
	}

	.all-concepts li button {
		border: none;
		background: none;
		text-align: left;
		padding: 0;
		color: var(--color-text-primary);
		font-size: 0.9375rem;
	}

	.all-concepts li button:hover {
		color: var(--color-cyan);
		box-shadow: none;
	}

	.confidence {
		color: var(--color-text-dim);
		font-size: 0.75rem;
		font-family: var(--font-mono);
	}

	.loading-text {
		color: var(--color-text-secondary);
		font-style: italic;
	}

	.error-text {
		color: #fca5a5;
		font-size: 0.875rem;
	}

	.no-results {
		color: var(--color-text-dim);
		font-style: italic;
		font-size: 0.875rem;
	}

	.related-list {
		list-style: none;
		padding: 0;
		margin-top: 0.5rem;
	}

	.related-list li {
		padding: 0.625rem;
		margin: 0.375rem 0;
		background: var(--color-bg-primary);
		border-radius: 6px;
		border: 1px solid var(--color-border);
		transition: all 0.2s ease;
	}

	.related-list li:hover {
		border-color: var(--color-teal);
		background: var(--color-teal-dark);
	}

	.related-list a {
		color: var(--color-cyan);
		text-decoration: none;
	}

	.related-list a:hover {
		text-shadow: 0 0 8px var(--color-glow-cyan);
	}

	/* Glowing concept highlighting - inspired by graphtech.dev */
	:global(.concept-cs) {
		background: rgba(77, 212, 220, 0.15);
		color: var(--color-cyan);
		padding: 0.125em 0.25em;
		border-radius: 3px;
		border-bottom: 2px solid var(--color-cyan);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	:global(.concept-cs:hover) {
		background: rgba(77, 212, 220, 0.25);
		box-shadow: 0 0 12px var(--color-glow-cyan);
	}

	:global(.concept-ai) {
		background: rgba(168, 85, 247, 0.15);
		color: var(--color-purple);
		padding: 0.125em 0.25em;
		border-radius: 3px;
		border-bottom: 2px solid var(--color-purple);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	:global(.concept-ai:hover) {
		background: rgba(168, 85, 247, 0.25);
		box-shadow: 0 0 12px var(--color-glow-purple);
	}

	:global(.concept-bio) {
		background: rgba(34, 197, 94, 0.15);
		color: #4ade80;
		padding: 0.125em 0.25em;
		border-radius: 3px;
		border-bottom: 2px solid #4ade80;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	:global(.concept-bio:hover) {
		background: rgba(34, 197, 94, 0.25);
		box-shadow: 0 0 12px rgba(34, 197, 94, 0.5);
	}

	:global(.concept-math) {
		background: rgba(251, 146, 60, 0.15);
		color: var(--color-orange);
		padding: 0.125em 0.25em;
		border-radius: 3px;
		border-bottom: 2px solid var(--color-orange);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	:global(.concept-math:hover) {
		background: rgba(251, 146, 60, 0.25);
		box-shadow: 0 0 12px var(--color-glow-orange);
	}

	:global(.concept-other) {
		background: rgba(156, 163, 175, 0.15);
		color: var(--color-text-secondary);
		padding: 0.125em 0.25em;
		border-radius: 3px;
		border-bottom: 2px solid var(--color-text-dim);
		cursor: pointer;
		transition: all 0.2s ease;
	}

	:global(.concept-other:hover) {
		background: rgba(156, 163, 175, 0.25);
		box-shadow: 0 0 8px rgba(156, 163, 175, 0.5);
	}

	/* Page actions - positioned in top right */
	.page-actions {
		position: fixed;
		top: 1rem;
		right: 2rem;
		z-index: 1000;
		display: flex;
		gap: 0.75rem;
	}

	.page-actions button {
		padding: 0.625rem 1.25rem;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		background: var(--color-bg-secondary);
		color: var(--color-text-secondary);
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.page-actions button:hover {
		background: var(--color-teal-dark);
		border-color: var(--color-teal);
		color: var(--color-cyan);
		box-shadow: 0 0 12px var(--color-glow-cyan);
	}

	/* Mobile responsive styles */
	@media (max-width: 768px) {
		.slop-view {
			flex-direction: column;
		}

		.main-content {
			padding: 2rem 1.5rem;
		}

		.sidebar {
			width: 100%;
			border-left: none;
			border-top: 1px solid var(--color-border);
		}

		.page-actions {
			top: 0.5rem;
			right: 1rem;
			gap: 0.5rem;
		}

		.page-actions button {
			padding: 0.5rem 0.875rem;
			font-size: 0.8125rem;
		}

		article :global(h1) {
			font-size: 2rem;
		}

		article :global(h2) {
			font-size: 1.5rem;
		}

		article :global(h3) {
			font-size: 1.25rem;
		}
	}
</style>
