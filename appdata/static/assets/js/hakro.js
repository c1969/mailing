function checkImage() {
	var _URL = window.URL || window.webkitURL;
	$("#file_logo").change(function (e) {
		var file, img;
		if ((file = this.files[0])) {
			img = new Image();
			var objectUrl = _URL.createObjectURL(file);
			img.onload = function () {
				alert(this.width + " " + this.height);
				_URL.revokeObjectURL(objectUrl);
			};
			img.src = objectUrl;
		}
	});
}

$(document).ready(function () {
	M.updateTextFields();
});

document.addEventListener("DOMContentLoaded", function () {
	var elems = document.querySelectorAll(".tooltipped");
	M.Tooltip.init(elems);
});

document.addEventListener("DOMContentLoaded", function () {
	var elems = document.querySelectorAll(".modal");
	M.Modal.init(elems);
});

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
	M.updateTextFields();
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
