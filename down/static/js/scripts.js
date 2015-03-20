/*
    WOW.js - Trigger animations
*/
new WOW().init();

$(function() {
  // Initialize the int'l phone number input.
  var $phone = $('#phone');
  $phone.intlTelInput({
    utilsScript: window.UTILS_SCRIPT,
    preferredCountries: ['us', 'ca', 'gb']
  });

  // Save the user's phone #.
  $phoneForm = $('#phone-form');
  $submitError = $('#submit-error');
  $invalidError = $('#invalid-error');

  $phoneForm.submit(function(e) {
    e.preventDefault();
    $submitError.hide();
    $invalidError.hide();

    if($phone.intlTelInput('isValidNumber')) {
      var phone = $phone.intlTelInput('getNumber');

      $.post('/api/phonenumbers', {phone: phone})
        .done(function() {
          phoneSaved();
        })
        .fail(function(jqXHR, textStatus) {
          if(jqXHR.status == 400) {
            phoneSaved();
          } else {
            $submitError.show();
          }
        });
    } else {
      $invalidError.show();
    }
  });

  function phoneSaved() {
    $phoneForm.hide();
    $('#success').show();
  };
});
