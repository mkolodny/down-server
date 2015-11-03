class FellowshipCtrl
  @$inject: ['$http', 'apiRoot']
  constructor: (@$http, @apiRoot) ->

  submit: (form) ->
    if not form.$valid then return


    postData =
      username: @username
      school: @school
    url = "#{@apiRoot}/fellowship-applications"
    @$http
      method: 'POST'
      url: url
      data: postData
    .then =>
      # Clear data, show success
      @username = undefined
      @school = undefined
      @success = true
    , =>
      # Show error
      @error = true



module.exports = FellowshipCtrl
