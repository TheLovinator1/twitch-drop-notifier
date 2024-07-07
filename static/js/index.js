// Create a new ScrollSpy instance that will track scroll position and update the active item in the table of contents
const scrollSpy = new bootstrap.ScrollSpy(document.body, {
    target: '.toc' // The target element that contains the table of contents
});

// Listen for the 'activate.bs.scrollspy' event, which is triggered when a new item becomes active in the table of contents
// This is needed because the toc can be longer than our screen and we want to scroll the active item into view
document.body.addEventListener('activate.bs.scrollspy', function (event) {
    // Find the currently active item in the table of contents
    const activeItem = document.querySelector('.toc .active');

    // If an active item is found, scroll it into view smoothly
    if (activeItem) {
        activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
    }
});
