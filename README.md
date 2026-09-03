# Settling: Women Who Sued the News

A digital archive documenting the EEOC lawsuit explosion against news organizations in the 1970s and its impact on women in media and public life.

## About

This project serves as a digital archive exploring the lawsuits filed under the EEOC against news organizations during the 1970s, focusing on the legal and social impact these cases had on the status of women in the workplace, media, and public life. It serves as a foundation for the forthcoming book "Settling: Women Who Sued the News" by Ashley Walter, PhD, and as a digital repository of oral histories and related materials.

## Site Structure

```
├── index.html              # Homepage with project overview
├── about.html              # About the project and book
├── contact.html            # Contact information
├── cases/                  # Landmark legal cases
│   ├── index.html         # Cases overview with table
│   ├── newsweek.html      # Newsweek case (1970)
│   ├── readers-digest.html # Reader's Digest case (1972)
│   ├── new-york-times.html # NY Times case (1974)
│   ├── washington-post.html # Washington Post case (1972)
│   └── associated-press.html # AP case (1973)
├── oral-histories/         # Oral history collections
│   └── index.html         # Oral histories overview
├── archive/                # Document archive
│   ├── index.html         # Archive overview
│   ├── oral-histories/    # Transcripts, audio, metadata
│   ├── photos/            # Open-license images
│   ├── court-documents/   # Complaints, settlements, orders
│   ├── press-clippings/   # News coverage
│   ├── personal-papers/   # Correspondence, memos
│   └── teaching-materials/ # Educational resources
├── styles.css             # Site-wide styles
└── .nojekyll             # Bypasses Jekyll processing

## Design Principles

- **No frameworks or large dependencies** - Pure HTML, CSS, and minimal JavaScript
- **Responsive design** - Mobile-first approach
- **Accessibility** - WCAG AA compliant color contrast, semantic HTML
- **Dublin Core metadata** - Standard metadata for all archival materials
- **Generated pages flagged** - All generated pages include `<meta name="generated" content="true">`

## Style Guide

### Color Palette
- **Primary**: Deep blue (#1A237E)
- **Accent**: Teal (#009688), Gold (#FFD600)
- **Text**: Charcoal (#212121)
- **Background**: White (#FFFFFF)

### Typography
- Sans-serif system fonts for maximum compatibility
- Minimum 16px body text
- Clear heading hierarchy

## Deployment

### GitHub Pages

This site is designed to be served through GitHub Pages:

1. Go to repository Settings → Pages
2. Set source to main branch
3. Site will be available at `https://centerfordigitalhumanities.github.io/settling/`

### Vercel Previews

Automatic Vercel deployments on pull requests:

- Every PR deploys a preview on Vercel
- Preview URLs appear in PR comments
- Review changes before merging

## Local Development

No build process required. Options:

1. **Simple**: Open `index.html` directly in a browser
2. **Server**: Run `python3 -m http.server 8000` and visit `http://localhost:8000`

## JavaScript Coding Style

See `.planning/coding-preferences.md` for detailed coding standards:

- Prefer ternaries, optional chaining, nullish coalescing
- Use guard clauses over nested conditionals
- Semicolons only when syntactically required
- Modern ES6+ patterns

## Contributing

To add content:

1. Create a new branch
2. Add HTML files following existing structure
3. Ensure all generated pages have `<meta name="generated" content="true">`
4. Submit a pull request
5. Review Vercel preview
6. Merge when approved

## Contact

**Dr. Ashley Walter**  
Email: ashley.walter@slu.edu  
Affiliation: Saint Louis University, Department of Communication

## License

Research Computing Group
