<script>
	import { onMount } from 'svelte';

	let slops = [];
	let loading = true;
	let error = null;

	onMount(async () => {
		try {
			// Fetch slops list from backend API
			const response = await fetch('http://localhost:8001/api/slops');
			if (!response.ok) {
				throw new Error(`Failed to load slops: ${response.statusText}`);
			}
			const data = await response.json();
			slops = data.slops || [];
		} catch (err) {
			error = err.message;
		} finally {
			loading = false;
		}
	});

	function formatDate(timestamp) {
		return new Date(timestamp * 1000).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<div class="index-page">
	<div class="hero">
		<h1>slop.at</h1>
		<p class="tagline">Semantic web publishing — where ideas connect</p>
	</div>

	<div class="slops-section">
		{#if loading}
			<div class="loading">Loading slops...</div>
		{:else if error}
			<div class="error">Error: {error}</div>
		{:else if slops.length > 0}
			<h2>Recent Slops</h2>
			<div class="slops-grid">
				{#each slops as slop}
					<a href="/{slop.hash}" class="slop-card">
						<h3>{slop.title}</h3>
						{#if slop.modified}
							<p class="date">{formatDate(slop.modified)}</p>
						{/if}
						{#if slop.concepts_count}
							<p class="meta">{slop.concepts_count} concepts</p>
						{/if}
					</a>
				{/each}
			</div>
		{:else}
			<div class="empty-state">
				<p>No slops yet!</p>
				<p class="hint">Submit your first slop via the MCP server or API.</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.index-page {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	.hero {
		text-align: center;
		padding: 4rem 2rem;
		margin-bottom: 3rem;
	}

	.hero h1 {
		font-family: var(--font-mono);
		font-size: 4rem;
		margin: 0;
		color: var(--color-cyan);
		text-shadow: 0 0 20px var(--color-glow-cyan);
		letter-spacing: -0.02em;
	}

	.tagline {
		font-family: var(--font-sans);
		font-size: 1.25rem;
		color: var(--color-text-secondary);
		margin-top: 1rem;
	}

	.slops-section {
		padding: 2rem 0;
	}

	.slops-section h2 {
		font-family: var(--font-sans);
		font-size: 1.5rem;
		margin-bottom: 2rem;
		color: var(--color-text-primary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.slops-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.slop-card {
		display: block;
		padding: 1.5rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		text-decoration: none;
		transition: all 0.2s ease;
	}

	.slop-card:hover {
		border-color: var(--color-teal);
		background: var(--color-teal-dark);
		box-shadow: 0 0 20px rgba(77, 212, 220, 0.2);
		transform: translateY(-2px);
	}

	.slop-card h3 {
		font-family: var(--font-sans);
		font-size: 1.25rem;
		margin: 0 0 0.75rem 0;
		color: var(--color-cyan);
	}

	.slop-card:hover h3 {
		text-shadow: 0 0 8px var(--color-glow-cyan);
	}

	.date {
		font-family: var(--font-mono);
		font-size: 0.875rem;
		color: var(--color-text-dim);
		margin: 0.5rem 0;
	}

	.meta {
		font-family: var(--font-mono);
		font-size: 0.8125rem;
		color: var(--color-text-secondary);
		margin: 0.5rem 0 0 0;
	}

	.loading, .error, .empty-state {
		text-align: center;
		padding: 3rem;
		background: var(--color-bg-secondary);
		border: 1px solid var(--color-border);
		border-radius: 8px;
		margin: 2rem 0;
	}

	.loading {
		color: var(--color-text-secondary);
	}

	.error {
		color: #fca5a5;
		border-color: rgba(220, 38, 38, 0.3);
	}

	.empty-state p {
		margin: 0.5rem 0;
		color: var(--color-text-secondary);
	}

	.hint {
		font-size: 0.9375rem;
		color: var(--color-text-dim);
		font-style: italic;
	}

	/* Mobile responsive styles */
	@media (max-width: 768px) {
		.index-page {
			padding: 1rem;
		}

		.hero {
			padding: 2rem 0;
		}

		.hero h1 {
			font-size: 2.5rem;
		}

		.tagline {
			font-size: 1rem;
		}

		.slops-grid {
			grid-template-columns: 1fr;
			gap: 1rem;
		}

		.slop-card {
			padding: 1.25rem;
		}

		.empty-state {
			padding: 2rem 1.5rem;
		}
	}
</style>
