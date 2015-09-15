# jquery must be loaded before angular - needed for intl-phone
window.$ = window.jQuery = require 'jquery'
require 'angular'
require './app-module'

# Tell AngularJS to go ahead and bootstrap when the DOM is loaded
angular.element(document).ready ->
  try
    angular.bootstrap document, ['down']
  catch error
    console.log error
    console.error error.stack or error.message or error
