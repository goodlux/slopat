<script>
	import '../app.css';
</script>

<div class="global-layout">
	<header class="site-header">
		<div class="header-inner">
			<div class="logo">
				<a href="/">
					<span class="logo-text">slop.at</span>
				</a>
			</div>
			<div class="header-actions">
				<slot name="header-actions" />
			</div>
		</div>
	</header>

	<main class="main-content">
		<slot />
	</main>

	<footer class="site-footer">
		<p>Semantic web publishing platform — SLOP first, optimize later</p>
	</footer>
</div>

<style>
	.global-layout {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.site-header {
		position: sticky;
		top: 0;
		z-index: 100;
		background: rgba(10, 13, 22, 0.8);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--color-border);
	}

	.header-inner {
		max-width: 1400px;
		margin: 0 auto;
		padding: 1rem 2rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.logo-text {
		font-family: var(--font-mono);
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--color-cyan);
		text-shadow: 0 0 10px var(--color-glow-cyan);
		letter-spacing: -0.02em;
	}

	.header-actions {
		display: flex;
		gap: 0.75rem;
		align-items: center;
	}

	.main-content {
		flex: 1;
		width: 100%;
	}

	.site-footer {
		padding: 2rem;
		text-align: center;
		font-size: 0.875rem;
		color: var(--color-text-dim);
		border-top: 1px solid var(--color-border);
		background: var(--color-bg-secondary);
	}
</style>
