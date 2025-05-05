function toggleLike(articleId) {
    fetch(`/article/${articleId}/like`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        const likeContainer = document.querySelector('.like-container');
        const likeCount = likeContainer.querySelector('.like-count');
        const likeText = likeContainer.querySelector('.like');    
        likeCount.textContent = data.likes;
        likeText.textContent = data.liked ? 'Liked' : 'Like';
        if (data.liked) {
            likeContainer.classList.add('liked');
        } else {
            likeContainer.classList.remove('liked');
        }
    });
}