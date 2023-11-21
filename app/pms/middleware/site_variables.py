def SiteVariableMiddleware(get_response):
    # One-time configuration and initialization.
    import time
    from site_variables.models import SiteVariableModel
    from django.core.cache import cache

    def middleware(request):
        tic = time.time()

        site_variables = cache.get('site_variables')
        
        if not site_variables:
            variables = SiteVariableModel.objects.all()
            site_variables = {}

            for variable in variables:
                site_variables[f'{variable.variable_name}'] = variable.variable_value

            cache.set('site_variables', site_variables, 15)
        # measure effect 
        # 11/21/23 : miss avg .03 to .05 / hit avg .001
        #     print(f'cach miss:{tic-time.time():.3f}') average .03-.05
        # else:
        #     print(f'cache hit:{tic-time.time():.3f}') average .001
        request.site_variables = site_variables
        response = get_response(request)

        return response

    return middleware