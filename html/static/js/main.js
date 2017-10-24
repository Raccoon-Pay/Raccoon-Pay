try { Typekit.load({ async: true }); } catch (e) { }
var temp;
var phoneEntryInput = document.getElementById('phone-entry').getElementsByTagName('input')[0];
var submitButton = document.getElementById('phone-entry').getElementsByTagName('button')[0];
phoneEntryInput.onkeydown = function () {
    temp = phoneEntryInput.value;
}
phoneEntryInput.oninput = function () {
    if (phoneEntryInput.value.match(/^\(\d\d\d\)$/) && temp.match(/^\(\d\d\d\)\ $/)) {
        phoneEntryInput.value = phoneEntryInput.value.slice(1, 3);
    }
    else if (phoneEntryInput.value.match(/^\(\d\d\d\)\ \d\d\d$/) && temp.match(/^\(\d\d\d\)\ \d\d\d\-$/)) {
        phoneEntryInput.value = phoneEntryInput.value.slice(0, 8);
    }
    else {
        var finalString = '';
        for (var i = 0; i < phoneEntryInput.value.length; i++) {
            if (phoneEntryInput.value.slice(i, i + 1).match(/^\d$/)) {
                finalString += phoneEntryInput.value.slice(i, i + 1);
            }
        }
        phoneEntryInput.value = finalString.slice(0, 10);
        if (phoneEntryInput.value.length === 10) {
            phoneEntryInput.value = '(' + phoneEntryInput.value.slice(0, 3) + ') ' + phoneEntryInput.value.slice(3, 6) + '-' + phoneEntryInput.value.slice(6, 10);
            submitButton.removeAttribute('disabled');
            submitButton.classList.remove('submit-disabled');
        }
        else if (phoneEntryInput.value.length >= 6) {
            phoneEntryInput.value = '(' + phoneEntryInput.value.slice(0, 3) + ') ' + phoneEntryInput.value.slice(3, 6) + '-' + phoneEntryInput.value.slice(6, 10);
            submitButton.setAttribute('disabled', 'disabled');
            submitButton.classList.add('submit-disabled');
        }
        else if (phoneEntryInput.value.length >= 3) {
            phoneEntryInput.value = '(' + phoneEntryInput.value.slice(0, 3) + ') ' + phoneEntryInput.value.slice(3, 6);
            submitButton.setAttribute('disabled', 'disabled');
            submitButton.classList.add('submit-disabled');
        }
    }
}
document.getElementById('about').onclick = function () {
    document.getElementById('popup').scrollTo(0, 0);
    document.getElementById('cover').classList.add('cover-opened');
    document.getElementById('popup').classList.add('popup-opened');
}
document.getElementById('cover').onclick = function () {
    document.getElementById('cover').classList.remove('cover-opened');
    document.getElementById('popup').classList.remove('popup-opened');
}