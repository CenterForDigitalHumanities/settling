# Settling: Women Who Sued the News

A simple archive for women's stories and resources related to legal action against news organizations.

## About

This project serves as a digital archive documenting the stories of women who have sued news organizations. It provides a platform to share their experiences and connect to relevant resources.

## Deployment

### GitHub Pages

This site is designed to be served through GitHub Pages. Once configured:

1. Go to your repository Settings
2. Navigate to Pages
3. Set the source to your main branch
4. The site will be available at `https://{username}.github.io/{repo-name}/`

### Vercel Previews

This repository is configured for automatic Vercel deployments on pull requests:

- Every PR to main will automatically deploy a preview on Vercel
- Preview URLs will be shared in the PR comments
- This allows you to review changes before merging to main

#### Setting up Vercel

1. Install the [Vercel for GitHub](https://vercel.com/docs/git/vercel-for-github) app
2. Import your repository in Vercel
3. Vercel will automatically detect the configuration from `vercel.json`
4. PRs will now get automatic preview deployments

## Structure

- `index.html` - Main page of the archive
- `styles.css` - Styling for the site
- `vercel.json` - Vercel deployment configuration
- `.nojekyll` - Bypasses Jekyll processing for GitHub Pages

## Contributing

To add stories or resources:

1. Create a new branch
2. Make your changes to the HTML files
3. Submit a pull request
4. Review the Vercel preview deployment
5. Once approved, merge to main

## Local Development

Simply open `index.html` in your web browser to view the site locally. No build process is required as this is a static HTML site.

## License

Center for Digital Humanities
