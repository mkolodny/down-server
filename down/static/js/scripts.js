$(function() {
  /*
   * iOS detection.
   */
  if(navigator.userAgent.match(/(iPad|iPhone|iPod)/g)) {
    $('.download').show();
  } else {
    setupPhones();
  }
  
  /*
   * Phone number input.
   */
  function setupPhones() {
    $('.request-invite').show();

    var $phones = $('.enter-phone');
    $phones.intlTelInput({
      utilsScript: window.UTILS_SCRIPT,
      preferredCountries: ['us', 'ca', 'gb']
    });

    // Save the user's phone #.
    $phoneForms = $('.phone-form');
    $submitError = $('.submit-error');
    $invalidError = $('.invalid-error');

    $phoneForms.submit(function(e) {
      e.preventDefault();
      $submitError.hide();
      $invalidError.hide();

      var $phoneForm = $(e.delegateTarget);
      var $phone = $phoneForm.find('.enter-phone');
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
  };

  function phoneSaved() {
    $phoneForms.hide();
    $('.success').show();
  };

  /*
    Wow
  */
  new WOW().init();
});
