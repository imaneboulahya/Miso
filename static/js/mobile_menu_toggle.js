const toggleButton = document.querySelector('.toggle-button');
        const navbarLinks = document.querySelector('.navbar-links');
        
        if (toggleButton) {
            toggleButton.addEventListener('click', () => {
                navbarLinks.classList.toggle('active');
            });
        }