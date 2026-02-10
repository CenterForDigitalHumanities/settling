# JavaScript Coding Preferences

## Modern Convenience Patterns
- Prefer ternaries over if/else for simple conditions
- Use switch statements for multiple conditions
- Use optional chaining (`?.`) for safe property access
- Use nullish coalescing operators (`??`) for default values
- Embrace modern ES6+ patterns for concise code

## Code Structure
- Use guard clauses instead of nested if/else
- Prefer scoped functions over global declarations
- Keep logic clear and readable
- Avoid long else patterns where efficient

## Semicolons
- Only include semicolons when syntax requires
- Do not use semicolons to terminate lines unnecessarily

## Examples

### Ternaries
```javascript
const value = condition ? ifTrue : ifFalse
```

### Optional Chaining
```javascript
const name = user?.profile?.name
```

### Nullish Coalescing
```javascript
const port = config.port ?? 3000
```

### Guard Clauses
```javascript
function processData(data) {
  if (!data) return
  if (!data.isValid) return
  
  // Main logic here
}
```

### Scoped Functions
```javascript
{
  const helperFunction = () => { /* ... */ }
  helperFunction()
}
```
