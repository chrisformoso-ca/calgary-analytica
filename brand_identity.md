# Calgary Analytica Brand Identity

## Brand Identity
- **Logo**: Red circular data visualization forming "C" shape
- **Personality**: Humble, curious, experimental, approachable
- **Voice**: Friendly yet professional, clear, accessible
- **Mindset**: "What if we tried...?" rather than "This is the answer"
- **Assets**: Store logos and brand files in `/assets/brand/`

## Design Philosophy
- **Minimalist but modern**: Clean, contemporary, no cruft
- **Core value first**: Ship the insight, not the decoration
- **Experimental**: Try things, iterate, learn in public
- **Solo dev reality**: Every element must earn its complexity
- **Less is more**: When in doubt, remove it

## Color Palette

### Core Colors
- **Calgary Red**: #E63946 (primary accent from logo)
- **Black**: #000000 (primary text)
- **White**: #FFFFFF (backgrounds)
- **Greys**: Use as needed for hierarchy and separation

### Usage Guidelines
- Red for primary actions, highlights, and data emphasis
- Greys for secondary information and borders
- Let Claude choose appropriate shades based on context
- Keep it simple and clean

## Typography
- **Font**: System font stack (clean and fast)
- **Hierarchy**: Clear size differences between levels
- **Readability**: Generous line height and spacing
- Let Claude choose appropriate sizes based on context

## Layout Principles
- **Desktop-first**: Optimize for 1920px
- **Clean structure**: Cards, clear sections, white space
- **Flexibility**: Let Claude determine specific spacing
- **Focus**: Data is the hero, design supports it

## Component Patterns

### Dashboard Cards
- White background with subtle shadows
- Consistent padding and spacing
- Simple borders or shadows for separation

### Data Visualizations
- Clean, uncluttered design
- Red for emphasis, greys for context
- Clear labels and legends
- Responsive sizing

### Interactive Elements
- Subtle hover states
- Clear active indicators
- Smooth transitions
- Focus on usability over effects

## D3.js Specific Guidelines

### Color Usage
- Use Calgary Red (#E63946) for primary data series
- Use grey variations for additional series
- Red gradients for heat maps and intensity
- Let Claude choose sensible colors for multi-series data

### Standard Margins
```javascript
const margin = {top: 40, right: 40, bottom: 60, left: 60};
```

### Responsive Pattern
```javascript
const container = d3.select('#chart');
const width = container.node().getBoundingClientRect().width;
const height = width * 0.6; // 60% aspect ratio
```

## Visual Guidelines
- **Typography**: Clean system fonts, clear hierarchy
- **Icons**: Simple when needed, red for active states
- **Spacing**: Consistent and generous
- **Data density**: High but readable
- **Animations**: Minimal and purposeful

## Best Practices
1. **Data first**: The visualization IS the design
2. **Quick experiments**: "Let's see if this works..."
3. **Accessibility**: Basic contrast and readability
4. **Performance**: Fast load > fancy effects
5. **Transparency**: Show sources, acknowledge limitations
6. **Copy**: Conversational, like explaining to a friend
7. **Iteration**: Launch minimal, improve based on use

## Copy Guidelines
- **Headers**: Questions and wonderings ("What if we looked at...?")
- **Explanations**: "Here's what we found..." not "The data shows..."
- **CTAs**: Gentle invitations ("Explore more" not "CLICK HERE")
- **Limitations**: Honest about what we don't know yet
- **Updates**: "New experiment:" or "We tried something different:"

## Implementation Philosophy
- **Start with nothing**: Add only what's needed
- **Modern minimalism**: Current design trends, minimal execution
- **Ship daily**: Better done than perfect
- **Experiment freely**: Try, measure, iterate
- **Trust the foundation**: Red + grey + white + data = enough

## Example Approach
```html
<!-- Minimal HTML, maximum value -->
<div class="card">
  <h3>What if we tracked Calgary home prices?</h3>
  <div class="metric">
    <span class="value">$525,000</span>
    <span class="label">Median Price</span>
    <span class="change">+5.2%</span>
  </div>
  <div id="chart"></div>
  <p class="note">Updated monthly from CREB data</p>
</div>
```

## Solo Dev Mindset
- **Every feature costs time**: Is it worth it?
- **Maintenance debt is real**: Simpler = sustainable
- **Modern but minimal**: Use current design patterns, implement simply
- **Learn in public**: Share experiments, failures, insights
- **AI partnership**: Let Claude handle complexity, you handle vision

Remember: You're one person with AI superpowers, not a team pretending to be one person.

Ship this. Make it better tomorrow.