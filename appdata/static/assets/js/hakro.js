document.addEventListener('DOMContentLoaded', function () {
  var elems = document.querySelectorAll('.modal');
  var instances = M.Modal.init(elems, options);
});

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

$(document).ready(function() {
  M.updateTextFields();
});