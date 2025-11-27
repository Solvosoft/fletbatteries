function initMyEditor(editorId, toolbar, height) {
    tinymce.init({
        selector: '#' + editorId,
        height: height,
        menubar: false,
        toolbar: toolbar + " | savebtn", // 🔹 agregamos el botón al final
        license_key: "gpl",
        plugins: "lists link image media table paste",
        setup: function (editor) {

            // 🔹 Definir el botón de guardar
            editor.ui.registry.addButton('savebtn', {
                text: 'Guardar',
                icon: 'save',
                onAction: function () {
                    const content = editor.getContent();

                    // Enviar al padre (Flet)
                    if (window.parent) {
                        window.parent.postMessage(JSON.stringify({
                            editor: editorId,
                            content: content,
                            action: "manual_save"
                        }), "*");
                    }

                    // Guardar en servidor
                    fetch(`http://localhost:8000/save_content?editor=${editorId}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ content: content })
                    }).then(() => {
                        console.log("Contenido guardado con éxito:", editorId);
                    }).catch(err => console.log("Error al guardar en servidor:", err));
                }
            });

            // 🔹 Guardado automático igual que antes
            editor.on('Change KeyUp', function () {
                const content = editor.getContent();
                if (window.parent) {
                    window.parent.postMessage(JSON.stringify({
                        editor: editorId,
                        content: content,
                        action: "autosave"
                    }), "*");
                }

                fetch(`http://localhost:8000/save_content?editor=${editorId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: content })
                }).catch(err => console.log("Error al guardar en servidor:", err));
            });
        }
    });
}