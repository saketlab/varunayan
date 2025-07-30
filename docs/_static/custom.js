// Custom JavaScript for Varunayan documentation

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced search functionality
    setupEnhancedSearch();
    
    // Add smooth scrolling to anchor links
    setupSmoothScrolling();
    
    // Add copy functionality to code blocks
    setupCodeCopy();
    
    // Add keyboard navigation
    setupKeyboardNavigation();
    
    // Add table of contents highlighting
    setupTocHighlighting();
    
    // Add loading animations
    setupLoadingAnimations();
    
    // Setup version switcher
    setupVersionSwitcher();
});

function setupEnhancedSearch() {
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        // Add search suggestions
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase();
            if (query.length > 2) {
                showSearchSuggestions(query);
            } else {
                hideSearchSuggestions();
            }
        });
        
        // Add search shortcuts
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });
    }
}

function showSearchSuggestions(query) {
    // This would integrate with Sphinx's search index
    // For now, we'll add a simple placeholder
    const suggestions = [
        'era5ify_geojson',
        'era5ify_bbox', 
        'era5ify_point',
        'search_variable',
        'describe_variables',
        'installation',
        'tutorials',
        'API reference'
    ].filter(item => item.toLowerCase().includes(query));
    
    // Display suggestions (implementation would depend on theme structure)
    console.log('Search suggestions:', suggestions);
}

function hideSearchSuggestions() {
    // Hide suggestion dropdown
}

function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

function setupCodeCopy() {
    // Add copy buttons to code blocks that don't have them
    document.querySelectorAll('pre:not(.highlight)').forEach(pre => {
        if (!pre.querySelector('.copybtn')) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copybtn';
            copyBtn.innerHTML = 'Copy';
            copyBtn.title = 'Copy to clipboard';
            copyBtn.style.position = 'absolute';
            copyBtn.style.top = '0.5rem';
            copyBtn.style.right = '0.5rem';
            
            pre.style.position = 'relative';
            pre.appendChild(copyBtn);
            
            copyBtn.addEventListener('click', function() {
                const code = pre.textContent || pre.innerText;
                navigator.clipboard.writeText(code).then(() => {
                    copyBtn.innerHTML = 'Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = 'Copy';
                    }, 2000);
                });
            });
        }
    });
}

function setupKeyboardNavigation() {
    document.addEventListener('keydown', function(e) {
        // Navigate with arrow keys
        if (e.altKey) {
            const currentPage = window.location.pathname;
            const navLinks = Array.from(document.querySelectorAll('.bd-sidebar a'));
            const currentIndex = navLinks.findIndex(link => link.href.includes(currentPage));
            
            if (e.key === 'ArrowLeft' && currentIndex > 0) {
                e.preventDefault();
                navLinks[currentIndex - 1].click();
            } else if (e.key === 'ArrowRight' && currentIndex < navLinks.length - 1) {
                e.preventDefault();
                navLinks[currentIndex + 1].click();
            }
        }
        
        // Toggle sidebar with 's' key
        if (e.key === 's' && !e.ctrlKey && !e.metaKey && !isInputFocused()) {
            e.preventDefault();
            toggleSidebar();
        }
        
        // Go to top with 't' key
        if (e.key === 't' && !e.ctrlKey && !e.metaKey && !isInputFocused()) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
}

function isInputFocused() {
    const activeElement = document.activeElement;
    return activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.contentEditable === 'true'
    );
}

function toggleSidebar() {
    const sidebar = document.querySelector('.bd-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('show');
    }
}

function setupTocHighlighting() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                const tocLink = document.querySelector(`.bd-toc a[href="#${id}"]`);
                if (tocLink) {
                    // Remove active class from all toc links
                    document.querySelectorAll('.bd-toc a').forEach(link => {
                        link.classList.remove('active');
                    });
                    // Add active class to current link
                    tocLink.classList.add('active');
                }
            }
        });
    }, {
        rootMargin: '-20% 0px -35% 0px'
    });
    
    // Observe all headings
    document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
        if (heading.id) {
            observer.observe(heading);
        }
    });
}

function setupLoadingAnimations() {
    // Add loading animation for large images
    document.querySelectorAll('img').forEach(img => {
        if (!img.complete) {
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease';
            
            img.onload = function() {
                this.style.opacity = '1';
            };
        }
    });
    
    // Add fade-in animation for content sections
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -10% 0px'
    };
    
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.admonition, .highlight, .table, .api-section').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        fadeObserver.observe(element);
    });
}

// Add search keyboard shortcut hint
function addSearchHint() {
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput && !searchInput.placeholder.includes('Ctrl+K')) {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const shortcut = isMac ? '⌘K' : 'Ctrl+K';
        searchInput.placeholder = `${searchInput.placeholder} (${shortcut})`;
    }
}

// Initialize search hint
document.addEventListener('DOMContentLoaded', addSearchHint);

// Version switcher functionality
function setupVersionSwitcher() {
    // Check if we're in a versioned documentation setup
    const currentPath = window.location.pathname;
    const versionMatch = currentPath.match(/\/(v\d+\.\d+\.\d+|main)\//);
    
    if (versionMatch) {
        const currentVersion = versionMatch[1];
        loadVersionSwitcher(currentVersion);
    }
}

function loadVersionSwitcher(currentVersion) {
    // Try to load versions.json
    fetch('/_static/versions.json')
        .then(response => response.json())
        .then(versions => {
            createVersionSwitcher(versions, currentVersion);
        })
        .catch(error => {
            // Fallback: try relative path
            fetch('../_static/versions.json')
                .then(response => response.json())
                .then(versions => {
                    createVersionSwitcher(versions, currentVersion);
                })
                .catch(error => {
                    console.log('No versions.json found, single version documentation');
                });
        });
}

function createVersionSwitcher(versions, currentVersion) {
    const navbar = document.querySelector('.bd-navbar');
    if (!navbar || versions.length <= 1) return;
    
    const switcherContainer = document.createElement('div');
    switcherContainer.className = 'version-switcher';
    switcherContainer.style.cssText = `
        position: relative;
        display: inline-block;
        margin-left: 1rem;
    `;
    
    const switcherButton = document.createElement('button');
    switcherButton.className = 'version-switcher-button';
    switcherButton.innerHTML = `Version ${currentVersion} ▼`;
    switcherButton.style.cssText = `
        background: var(--bs-primary);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.25rem 0.75rem;
        font-size: 0.875rem;
        cursor: pointer;
        transition: background-color 0.2s;
    `;
    
    const dropdown = document.createElement('div');
    dropdown.className = 'version-dropdown';
    dropdown.style.cssText = `
        position: absolute;
        top: 100%;
        right: 0;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        min-width: 150px;
        z-index: 1000;
        display: none;
    `;
    
    versions.forEach(version => {
        const link = document.createElement('a');
        link.href = version.url;
        link.textContent = version.name;
        link.style.cssText = `
            display: block;
            padding: 0.5rem 0.75rem;
            color: #333;
            text-decoration: none;
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s;
        `;
        
        if (version.version === currentVersion) {
            link.style.backgroundColor = '#f8f9fa';
            link.style.fontWeight = 'bold';
        }
        
        link.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#e9ecef';
        });
        
        link.addEventListener('mouseleave', function() {
            if (version.version !== currentVersion) {
                this.style.backgroundColor = 'white';
            }
        });
        
        dropdown.appendChild(link);
    });
    
    switcherButton.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
    });
    
    document.addEventListener('click', function() {
        dropdown.style.display = 'none';
    });
    
    switcherContainer.appendChild(switcherButton);
    switcherContainer.appendChild(dropdown);
    
    // Add to navbar
    const navbarNav = navbar.querySelector('.navbar-nav');
    if (navbarNav) {
        navbarNav.appendChild(switcherContainer);
    }
}