function deletedItem(idItem) {
    document.getElementById(idItem).remove();
}

flag1 = 1;
flag2 = 1;
flag3 = 1;

function show_spinner1() {
    document.getElementById("spinner1").style.visibility = "visible";
    flag1 = 0;
  }
function show_spinner2() {
    document.getElementById("spinner2").style.visibility = "visible";
    flag2 = 0;
  }
function show_spinner3() {
    document.getElementById("spinner3").style.visibility = "visible";
    flag3 = 0;
  }