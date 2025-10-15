 // Make the indicator move when a menu item is clicked
    const list = document.querySelectorAll('.navigation ul li');
    function activeLink() {
        list.forEach(item => item.classList.remove('active'));
        this.classList.add('active');
    }
    list.forEach(item => item.addEventListener('click', activeLink));

    //Make the nav bar stop before the footer
const navbar = document.querySelector('.navbar');
const footer = document.querySelector('footer');

window.addEventListener('scroll', () => {
    const footerRect = footer.getBoundingClientRect();
    const navbarHeight = navbar.offsetHeight;

  // Stop navbar above the footer
    if (footerRect.top < window.innerHeight) {
        navbar.style.position = 'absolute';
        navbar.style.bottom = 'auto';
        navbar.style.top = `${window.scrollY + footerRect.top - navbarHeight}px`;
    } else {
        navbar.style.position = 'fixed';
        navbar.style.bottom = '0';
        navbar.style.top = 'auto';
    }
});

AOS.init({
    duration: 1200, 
    once: true,  
    easing: 'ease-out-quart'
});
