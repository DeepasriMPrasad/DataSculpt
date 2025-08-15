import { Session } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

export async function loadSingleFile(session: Session) {
  try {
    // Try to load SingleFile as extension first
    const extensionPath = findSingleFileExtension();
    if (extensionPath && fs.existsSync(extensionPath)) {
      await session.loadExtension(extensionPath);
      console.log('SingleFile extension loaded');
      return;
    }
    
    // Fallback: inject SingleFile core script
    await injectSingleFileCore(session);
    console.log('SingleFile core injected');
  } catch (error) {
    console.error('Failed to load SingleFile:', error);
    throw error;
  }
}

function findSingleFileExtension(): string | null {
  // Common paths where SingleFile extension might be installed
  const possiblePaths = [
    path.join(process.env.HOME || '', '.config/chromium/Default/Extensions/mpiodijhokgodhhofbcjdecpffjipkle'),
    path.join(process.env.HOME || '', '.config/google-chrome/Default/Extensions/mpiodijhokgodhhofbcjdecpffjipkle'),
    path.join(__dirname, '../../../assets/singlefile-extension')
  ];
  
  for (const basePath of possiblePaths) {
    if (fs.existsSync(basePath)) {
      // Find the latest version directory
      const versions = fs.readdirSync(basePath).filter(name => /^\d+\.\d+\.\d+/.test(name));
      if (versions.length > 0) {
        versions.sort();
        return path.join(basePath, versions[versions.length - 1]);
      }
    }
  }
  
  return null;
}

async function injectSingleFileCore(session: Session) {
  // Inject SingleFile core functionality
  const singleFileCore = `
    window.singlefile = {
      processCurrentPage: function() {
        // Basic HTML capture - in production, this would be the actual SingleFile core
        const html = document.documentElement.outerHTML;
        
        // Inline all CSS and resources
        const inlinedHtml = this.inlineResources(html);
        return inlinedHtml;
      },
      
      inlineResources: function(html) {
        // Simplified resource inlining
        // In production, this would handle CSS, images, fonts, etc.
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Inline CSS
        const stylesheets = doc.querySelectorAll('link[rel="stylesheet"]');
        stylesheets.forEach(link => {
          // In production, fetch and inline CSS content
          link.remove();
        });
        
        // Convert relative URLs to absolute
        const baseUrl = window.location.href;
        const elements = doc.querySelectorAll('[src], [href]');
        elements.forEach(el => {
          const attr = el.hasAttribute('src') ? 'src' : 'href';
          const url = el.getAttribute(attr);
          if (url && !url.startsWith('http') && !url.startsWith('data:')) {
            el.setAttribute(attr, new URL(url, baseUrl).href);
          }
        });
        
        return doc.documentElement.outerHTML;
      }
    };
    
    console.log('SingleFile core loaded');
  `;
  
  // Inject the script into all web contents
  session.webContents.getAllWebContents().forEach(webContents => {
    webContents.executeJavaScript(singleFileCore);
  });
  
  // Also inject into future web contents
  session.webContents.on('did-finish-load', (webContents) => {
    webContents.executeJavaScript(singleFileCore);
  });
}
