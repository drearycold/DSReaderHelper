from calibre.srv.routes import endpoint, json

@endpoint('/dshelper/status/{job_id}', types={'job_id': int}, auth_required=True, postprocess=json)
def dshelper_status(ctx, rd, job_id):
    job_status = ctx.job_status(job_id)
    return job_status