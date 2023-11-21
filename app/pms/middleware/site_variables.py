def SiteVariableMiddleware(get_response):
    # One-time configuration and initialization.
    from site_variables.models import SiteVariableModel
    from django.core.cache import cache

    def middleware(request):

        site_variables = cache.get('site_variables')
        
        if not site_variables:
            variables = SiteVariableModel.objects.all()
            site_variables = {}

            for variable in variables:
                site_variables[f'{variable.variable_name}'] = variable.variable_value

            cache.set('site_variables', site_variables, 10)
        
        request.site_variables = site_variables
        response = get_response(request)

        return response

    return middleware