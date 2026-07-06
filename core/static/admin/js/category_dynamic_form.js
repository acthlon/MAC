(function() {
    'use strict';

    function init() {
        const targetModelSelect = document.getElementById('id_target_model');
        const nameField = document.getElementById('id_name');
        if (!targetModelSelect || !nameField) return;

        // Debugging logs to help check the console
        const productChoicesAttr = targetModelSelect.getAttribute('data-product-choices');
        const materialChoicesAttr = targetModelSelect.getAttribute('data-material-choices');
        console.log('Django Dynamic Form Debug:', {
            targetModelSelectElement: targetModelSelect,
            productChoicesAttr: productChoicesAttr,
            materialChoicesAttr: materialChoicesAttr
        });

        // Parse attributes, with a fallback list in case Django didn't render the attributes yet
        const productChoices = productChoicesAttr ? JSON.parse(productChoicesAttr) : [
            { value: 'DRESS', label: 'Dress' },
            { value: 'GOWN', label: 'Gown' },
            { value: 'KAFTAN', label: 'Kaftan' },
            { value: 'ABAYA', label: 'Abaya' },
            { value: 'BOUBOU', label: 'Boubou' },
            { value: 'JUMPSUIT', label: 'Jumpsuit' },
            { value: 'TWO_PIECE', label: 'Two Piece Set' },
            { value: 'ACCESSORY', label: 'Accessory' }
        ];

        const materialChoices = materialChoicesAttr ? JSON.parse(materialChoicesAttr) : [
            { value: 'ANKARA', label: 'Ankara' },
            { value: 'SILK', label: 'Silk' },
            { value: 'LACE', label: 'Lace' }
        ];

        function updateNameField() {
            const selectedOption = targetModelSelect.options[targetModelSelect.selectedIndex];
            const selectedText = selectedOption ? selectedOption.textContent.toLowerCase() : '';
            const currentNameField = document.getElementById('id_name');
            if (!currentNameField) return;

            let choices = null;
            if (selectedText.includes('product')) {
                choices = productChoices;
            } else if (selectedText.includes('material')) {
                choices = materialChoices;
            }

            const currentValue = currentNameField.value;

            if (choices) {
                let selectElement;
                if (currentNameField.tagName === 'SELECT') {
                    selectElement = currentNameField;
                    selectElement.innerHTML = '';
                } else {
                    selectElement = document.createElement('select');
                    selectElement.id = 'id_name';
                    selectElement.name = 'name';
                    selectElement.className = currentNameField.className;
                    currentNameField.parentNode.replaceChild(selectElement, currentNameField);
                }

                const defaultOpt = document.createElement('option');
                defaultOpt.value = '';
                defaultOpt.textContent = '---------';
                selectElement.appendChild(defaultOpt);

                choices.forEach(choice => {
                    const opt = document.createElement('option');
                    opt.value = choice.value;
                    opt.textContent = choice.label;
                    if (choice.value === currentValue) {
                        opt.selected = true;
                    }
                    selectElement.appendChild(opt);
                });
            } else {
                if (currentNameField.tagName === 'SELECT') {
                    const inputElement = document.createElement('input');
                    inputElement.type = 'text';
                    inputElement.id = 'id_name';
                    inputElement.name = 'name';
                    inputElement.className = currentNameField.className;
                    inputElement.maxLength = 200;
                    inputElement.value = currentValue;
                    currentNameField.parentNode.replaceChild(inputElement, currentNameField);
                }
            }
        }

        targetModelSelect.addEventListener('change', updateNameField);
        updateNameField();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
