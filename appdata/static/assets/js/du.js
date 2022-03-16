const checkRequiredInput = (checkbox, inputId) => {
	const input = document.getElementById(inputId);
	input.disabled = !checkbox.checked;
	if (checkbox.checked) {
		input.attributes.required = true;
		input.classList.add("validate");
	} else {
		input.value = null;
		input.attributes.required = false;
		input.classList.remove("validate");
		input.classList.remove("invalid");
		input.classList.remove("valid");
	}
	toggleShirtCheckbox();
};

const toggleShirtCheckbox = () => {
	const email = document.getElementById("email");
	const phone = document.getElementById("callme");

	const shirt = document.getElementById("shirt");
	const isContactInfoChecked = email.checked || phone.checked;
	shirt.disabled = !isContactInfoChecked;
	if (!isContactInfoChecked) {
		shirt.checked = false;
	}
};
