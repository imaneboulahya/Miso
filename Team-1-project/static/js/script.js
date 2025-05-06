const toggleButton = document.getElementsByClassName('toggle-button')[0]
const navbarLinks = document.getElementsByClassName('navbar-links')[0]

toggleButton.addEventListener('click', () => {
  navbarLinks.classList.toggle('active')
})
function clearPlaceholder() {
  const editor = document.getElementById("editor");
  if (editor.innerText === "Commencez à écrire votre article ici...") {
    editor.innerText = ""; // Clear the placeholder when focused
  }
}

function restorePlaceholderIfEmpty() {
  const editor = document.getElementById("editor");
  if (editor.innerText.trim() === "") {
    editor.innerText = "Commencez à écrire votre article ici..."; // Restore if empty
  }
}

function updateStatus() {
  const editor = document.getElementById("editor");
  let text = editor.innerText;
  
  // Ignore counting if the text is still the placeholder
  if (text === "Commencez à écrire votre article ici...") {
    document.getElementById("word-count").innerText = "0 mot, 0 caractère";
    return;
  }

  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  const characters = text.replace(/\s/g, '');
  
  document.getElementById("word-count").innerText =
    `${words.length} mot${words.length > 1 ? 's' : ''}, ${characters.length} caractère${characters.length > 1 ? 's' : ''}`;
  
  document.getElementById("last-modified").innerText =
    "Dernière modification : " + new Date().toLocaleTimeString();
}
document.addEventListener("DOMContentLoaded", function() {
  const editor = document.getElementById("editor");
  if (editor.innerText.trim() === "") {
    editor.innerText = "Commencez à écrire votre article ici...";
  }
  updateStatus();
});
document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.add('animating');
  setTimeout(function() {
      document.body.classList.remove('animating');
      document.querySelector('.fullscreen-loader').remove();
  }, 3000);
});
function toggleLike(articleId) {
  fetch(`/article/${articleId}/like`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      }
  })
  .then(response => response.json())
  .then(data => {
      const likeContainer = document.querySelector(`.like-container[onclick="toggleLike(${articleId})"]`);
      const likeCount = likeContainer.querySelector('.like-count');
      const likeText = likeContainer.querySelector('.like');
      
      likeCount.textContent = data.likes;
      
      if (likeText.textContent.trim() === 'Like') {
          likeText.textContent = 'Liked';
          likeText.classList.add('active');
      } else {
          likeText.textContent = 'Like';
          likeText.classList.remove('active');
      }
  })
  .catch(error => {
      console.error('Error:', error);
  });
}