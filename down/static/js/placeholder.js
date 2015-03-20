
$(document).ready(function(){
	
	$('.contact-email, .contact-subject, .contact-message, .subscribe-email').removeAttr('placeholder');
	
	$('.contact-email').val('Email...');
	$('.contact-subject').val('Subject...');
	$('.contact-message').text('Message...');
	
	$('.subscribe-email').val('Enter your email...');
	
});