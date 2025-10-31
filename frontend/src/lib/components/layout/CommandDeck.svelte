<!--
	CommandDeck V2 - Immersive Cockpit Layout
	TopBar eliminated - MasterControlRack becomes the supreme command center
	Sticky behavior implemented at page level for optimal UX
-->
<div class="command-deck-v2">
	<div class="rack-nav-area"><slot name="rack-nav" /></div>
	<div class="main-canvas-area"><slot name="main-canvas" /></div>
</div>
