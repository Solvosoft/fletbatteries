tinymce.init({
                 selector: '#mytextarea',
                 plugins: 'lists link image code',
                 toolbar: 'undo redo | bold italic | alignleft aligncenter alignright | code',

             // Cargar
contenido
desde
backend
init_instance_callback: function(editor)
{
    fetch("http://127.0.0.1:5000/load")
    .then(res= > res.json())
.then(data= > editor.setContent(data.content));
},

// Guardar
contenido
en
backend
setup: function(editor)
{
    editor.on("change", function()
{
    fetch("http://127.0.0.1:5000/save", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            title: title,
            content: editor.getContent()
        })
    });
});
}
});