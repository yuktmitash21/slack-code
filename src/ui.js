document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    const sidebarToggle = document.createElement('button');
    sidebarToggle.textContent = 'Toggle Sidebar';
    sidebarToggle.style.position = 'fixed';
    sidebarToggle.style.bottom = '20px';
    sidebarToggle.style.right = '20px';
    document.body.appendChild(sidebarToggle);

    sidebarToggle.addEventListener('click', function() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.style.display = sidebar.style.display === 'none' ? 'block' : 'none';
        }
    });
});