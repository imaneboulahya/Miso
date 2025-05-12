document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        if (e.target.closest('.like-btn')) {
            const likeBtn = e.target.closest('.like-btn');
            const articleId = likeBtn.getAttribute('data-article-id');
            toggleLike(articleId);
        }
    });
    function toggleLike(articleId) {
        fetch('/check_auth')
            .then(response => response.json())
            .then(data => {
                if (!data.authenticated) {
                    window.location.href = '/login';
                    return;
                }
                const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
                fetch(`/article/${articleId}/like`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    const likeBtn = document.querySelector(`.like-btn[data-article-id="${articleId}"]`);
                    const likeCount = likeBtn.querySelector('.like-count');
                    const likeText = likeBtn.querySelector('.like-text');
                    likeCount.textContent = data.likes;
                    likeText.textContent = data.liked ? 'Liked' : 'Like';
                    likeBtn.classList.toggle('liked', data.liked);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error processing like. Please try again.');
                });
            });
    }
});