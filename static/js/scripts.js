function deletedItem(idItem) {
    document.getElementById(idItem).remove();
}

flag1 = 1;
flag2 = 1;
flag3 = 1;

function show_spinner(spinner) {
    document.getElementById(spinner).style.visibility = "visible";
    if (spinner == 'spiner1'){
      flag1 = 0;
    } else if (spinner == 'spiner2'){
      flag2 = 0;
    } else if(spinner == 'spiner3'){
      flag3 = 0;  
    }
}
