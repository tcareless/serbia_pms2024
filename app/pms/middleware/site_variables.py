def SiteVariableMiddleware(get_response):
    # One-time configuration and initialization.
    from site_variables.models import SiteVariableModel

    def middleware(request):

        variables = SiteVariableModel.objects.all()
        site_variables = {}

        for variable in variables:
            site_variables[f'{variable.variable_name}'] = variable.variable_value

        ##  TODO: cache site_variables for 10 seconds
        request.site_variables = site_variables
        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware