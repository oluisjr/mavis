// Este script controla a interatividade do título MAVIS.
function toggleMavis() {
    // Seleciona todos os elementos de texto que estão escondidos.
    const hiddenTexts = document.querySelectorAll('.mavis-hidden-text');
    
    // Para cada elemento encontrado, alterna a classe 'expanded'.
    // A classe 'expanded' é definida no style.css e controla a visibilidade.
    hiddenTexts.forEach(text => {
        text.classList.toggle('expanded');
    });
}