function execCmd(command) {
    document.execCommand(command, false, null);
    updateStatus();
  }

  function execCmdWithArg(command, arg) {
    document.execCommand(command, false, arg);
    updateStatus();
  }

  function insertLink() {
    const url = prompt("Entrez l'URL du lien :", "https://");
    if (url) execCmdWithArg('createLink', url);
  }

  function insertImage() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = function () {
      const file = input.files[0];
      const reader = new FileReader();
      reader.onload = function (e) {
        execCmdWithArg('insertImage', e.target.result);
      };
      reader.readAsDataURL(file);
    };
    input.click();
  }

  function toggleDarkMode() {
    document.body.classList.toggle('dark');
  }

  function updateStatus() {
    const text = document.getElementById("editor").innerText;
    const words = text.trim().split(/\s+/).filter(w => w.length > 0);
    const characters = text.replace(/\s/g, '');
    document.getElementById("word-count").innerText =
      `${words.length} mot${words.length > 1 ? 's' : ''}, ${characters.length} caractère${characters.length > 1 ? 's' : ''}`;
    document.getElementById("last-modified").innerText =
      "Dernière modification : " + new Date().toLocaleTimeString();
    document.getElementById('hidden-content').value = document.getElementById('editor').innerHTML;
  }

  document.addEventListener("DOMContentLoaded", updateStatus);
  document.getElementById('article-form').addEventListener('submit', function(e) {
    const htmlContent = document.getElementById('editor').innerHTML;
    document.getElementById('content').value = htmlContent;
    if (document.getElementById('editor').innerText.trim().length < 10) {
        e.preventDefault();
        alert('Veuillez écrire un article plus long (au moins 10 caractères)');
        return false;
    }
    if (!document.getElementById('category').value) {
        e.preventDefault();
        alert('Veuillez sélectionner une catégorie');
        return false;
    }
    return true;
});
window.addEventListener('DOMContentLoaded', function() {
    updateStatus();
});
function execCmd(command) {
    document.execCommand(command, false, null);
    updateStatus();
}
function execCmdWithArg(command, arg) {
    document.execCommand(command, false, arg);
    updateStatus();
}
function insertLink() {
    const url = prompt('Entrez le lien URL:');
    if (url) {
        document.execCommand('createLink', false, url);
        updateStatus();
    }
}
function insertImage() {
    const url = prompt('Entrez l\'URL de l\'image:');
    if (url) {
        document.execCommand('insertImage', false, url);
        updateStatus();
    }
}
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
}
function updateStatus() {
    const text = document.getElementById('editor').innerText;
    const wordCount = text.trim() === '' ? 0 : text.trim().split(/\s+/).length;
    const charCount = text.length;
    
    document.getElementById('word-count').textContent = 
        `${wordCount} mots, ${charCount} caractères`;
    
    document.getElementById('last-modified').textContent = 
        `Dernière modification : ${new Date().toLocaleTimeString()}`;
}
function clearPlaceholder() {
    const editor = document.getElementById('editor');
    if (editor.innerHTML === 'Commencez à écrire votre article ici...') {
        editor.innerHTML = '';
    }
}     
function restorePlaceholderIfEmpty() {
    const editor = document.getElementById('editor');
    if (editor.innerHTML === '' || editor.innerText.trim() === '') {
        editor.innerHTML = 'Commencez à écrire votre article ici...';
    }
}
document.getElementById('article-form').addEventListener('submit', function(e) {
  const editor = document.getElementById('editor');
  const textContent = editor.innerText || editor.textContent;
  const cleanHTML = cleanEditorContent(editor.innerHTML);
  document.getElementById('content').value = cleanHTML;
  if (textContent.trim().length < 10) {
      e.preventDefault();
      alert('Veuillez écrire un article plus long (au moins 10 caractères)');
      return false;
  }
  if (!document.getElementById('category').value) {
      e.preventDefault();
      alert('Veuillez sélectionner une catégorie');
      return false;
  }
  return true;
});
function cleanEditorContent(html) {
  const temp = document.createElement('div');
  temp.innerHTML = html;
  const allowedTags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'img'];
  const elements = temp.querySelectorAll('*');
  elements.forEach(el => {
      if (!allowedTags.includes(el.tagName.toLowerCase())) {
          const content = document.createTextNode(el.textContent);
          el.parentNode.replaceChild(content, el);
      }
  }); 
  return temp.innerHTML;
}