// Global variables for navigation
let currentGalleryImages = [];
let currentImageIndex = -1;

function maximizeImage(img) {
    const overlay = document.getElementById('maximizedOverlay');
    const maximizedImg = document.getElementById('maximizedImg');
    
    // Get all gallery images
    const galleryImages = document.querySelectorAll('.gallery-image');
    currentGalleryImages = Array.from(galleryImages);
    
    // Find the index of the clicked image
    currentImageIndex = currentGalleryImages.findIndex(image => image.src === img.src);
    
    // Update the maximized image
    maximizedImg.src = img.src;
    maximizedImg.alt = img.alt;
    overlay.style.display = 'flex';
    
    // Update navigation arrows and counter
    updateNavigation();
    
    // Prevent click event from bubbling to overlay
    maximizedImg.onclick = function(event) {
        event.stopPropagation();
    };
}

function minimizeImage() {
    const overlay = document.getElementById('maximizedOverlay');
    overlay.style.display = 'none';
    
    // Reset navigation
    currentGalleryImages = [];
    currentImageIndex = -1;
}

function navigateImage(direction) {
    if (currentGalleryImages.length === 0) return;
    
    // Calculate new index
    if (direction === 'next') {
        currentImageIndex = (currentImageIndex + 1) % currentGalleryImages.length;
    } else if (direction === 'prev') {
        currentImageIndex = (currentImageIndex - 1 + currentGalleryImages.length) % currentGalleryImages.length;
    }
    
    // Update the maximized image
    const maximizedImg = document.getElementById('maximizedImg');
    const newImage = currentGalleryImages[currentImageIndex];
    
    maximizedImg.src = newImage.src;
    maximizedImg.alt = newImage.alt;
    
    // Update navigation arrows and counter
    updateNavigation();
    
    // Prevent click event from bubbling to overlay
    maximizedImg.onclick = function(event) {
        event.stopPropagation();
    };
}

function updateNavigation() {
    const prevArrow = document.getElementById('prevArrow');
    const nextArrow = document.getElementById('nextArrow');
    const imageCounter = document.getElementById('imageCounter');
    
    if (prevArrow && nextArrow && imageCounter) {
        // Update counter
        imageCounter.textContent = `${currentImageIndex + 1} / ${currentGalleryImages.length}`;
        
        // Always show arrows if there are multiple images
        prevArrow.style.display = currentGalleryImages.length > 1 ? 'block' : 'none';
        nextArrow.style.display = currentGalleryImages.length > 1 ? 'block' : 'none';
    }
}

// Close with ESC key, navigate with arrow keys
document.addEventListener('keydown', function(event) {
    const overlay = document.getElementById('maximizedOverlay');
    
    if (overlay.style.display === 'flex') {
        switch(event.key) {
            case 'Escape':
                minimizeImage();
                break;
            case 'ArrowLeft':
                navigateImage('prev');
                event.preventDefault(); // Prevent page scrolling
                break;
            case 'ArrowRight':
                navigateImage('next');
                event.preventDefault(); // Prevent page scrolling
                break;
        }
    }
});

// Add touch swipe support for mobile
let touchStartX = 0;
let touchEndX = 0;

document.getElementById('maximizedOverlay').addEventListener('touchstart', function(event) {
    touchStartX = event.changedTouches[0].screenX;
}, false);

document.getElementById('maximizedOverlay').addEventListener('touchend', function(event) {
    touchEndX = event.changedTouches[0].screenX;
    handleSwipe();
}, false);

function handleSwipe() {
    const swipeThreshold = 50; // Minimum swipe distance in pixels
    
    if (touchStartX - touchEndX > swipeThreshold) {
        // Swipe left -> next image
        navigateImage('next');
    } else if (touchEndX - touchStartX > swipeThreshold) {
        // Swipe right -> previous image
        navigateImage('prev');
    }
}