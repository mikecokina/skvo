def prepare_message():
    pass


def get_photometry_loader(transform=None, init_sink=None):

    def load_photometry(start_date=None, end_date=None, **kwargs):
        sink = init_sink(**kwargs)
        sink()
    return load_photometry
