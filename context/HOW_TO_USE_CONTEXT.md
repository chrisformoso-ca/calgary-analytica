# How to Use Context Management

## Starting a New Session (Updated with Custom Slash Commands)

### Option 1: Smart Session Start (Recommended)
```
/project:start
# Automatically checks for next-session.md and loads it, or shows context menu
```

### Option 2: Specific Context Loading  
```
/project:load dashboard    # Load context-dashboard.md for UI work
/project:load pipeline     # Load context-data-pipeline.md for data work
/project:load general      # Load context-general.md for overview
/project:load continue     # Load next-session.md to resume previous work
```

### Option 3: Legacy Manual Loading (Still Supported)
```
"Load context-dashboard.md - let's build the housing dashboard"
"Load context-data-pipeline.md - I have the June 2025 PDF"  
"Load context-general.md"
```

## Cost Comparison

### Old Way (DON'T DO THIS)
```
"Read README.md, core_strategy.md, brand_identity.md, and phase-1-mvp-spec.md"
Cost: ~20,000 tokens = ~$0.20/session
```

### New Way (DO THIS)
```
/project:load dashboard
Cost: ~2,000 tokens = ~$0.02/session
```

## Savings
- **90% reduction** in context costs
- **More focused** sessions
- **Faster** responses
- **Cleaner** context window

## Examples

### Dashboard Work
```
You: /project:load dashboard
Claude: [Loads 25 lines instead of 1,000+]
```

### Monthly Update
```  
You: /project:update month 2025-06
Claude: [Loads pipeline context + processes June data with validation]
```

### Session Management
```
You: /project:start
Claude: [Smart initialization - loads next-session.md or shows context menu]

You: /project:save  
Claude: [Creates session summary + updates next-session.md automatically]
```

### Quick Help
```
You: /project:help
Claude: [Shows command reference without loading heavy documentation]
```

## Tips
1. Use `/project:start` to begin any session - it's intelligent and cost-effective
2. Use `/project:save` to end sessions - it handles next-session.md automatically  
3. Use `/project:help` when you forget commands - quick reference without token cost
4. Archive completed phase docs  
5. Keep contexts under 50 lines each for maximum efficiency

## Quick Command Reference
- `/project:start` - Smart session initialization
- `/project:save` - Automated session end + next-session.md update
- `/project:load [context]` - Load specific context files
- `/project:help` - Command reference
- `/project:update month YYYY-MM` - Process monthly data
- `/project:dashboard create [name]` - Create dashboard structure