class BannerRouter:
    """
    A router to control all database operations on models in the
    banner application.
    """
    # https://docs.djangoproject.com/en/2.2/topics/db/multi-db/
    def db_for_read(self, model, **hints):
        """
        Attempts to read banner models go to the banner db.
        """
        if model._meta.app_label == 'banner':
            return 'banner'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write banner models go to the banner db.
        """
        if model._meta.app_label == 'banner':
            return 'banner'
        return None

    # def allow_relation(self, obj1, obj2, **hints):
    #     """
    #     Allow relations if a model in the auth app is involved.
    #     """
    #     if obj1._meta.app_label == 'auth' or \
    #        obj2._meta.app_label == 'auth':
    #        return True
    #     return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the banner app only appears in the 'banner'
        database.
        """
        #print(app_label)
        # at the moment we have the following (I believe):
        # - auth tables go in ichair.db and banner.db
        # - contenttypes go in both
        # - sites go in both
        # - admin goes in both
        # - sessions goes in both
        # - planner app models go in ichair.db
        # - banner app models go in banner.db
        # ...not sure if all of this needs to go in banner, but it's probably OK...(?) 
        # ...could further restrict what goes into banner.db 
        #print('model: ', model_name)
        #print('db: ', db)
        if app_label == 'banner':
            #print('it is banner!')
            return db == 'banner'
        elif app_label == 'planner':
            #print('it is planner!')
            return db == 'default'
        return None