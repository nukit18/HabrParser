from django.db import models


class StatusChoices(models.TextChoices):
    PROCESSED = 'processed'
    ERROR = 'error'
    AT_WORK = 'at_work'


class HabrHubs(models.Model):
    name = models.CharField(max_length=50, null=True)
    hub_link = models.CharField(max_length=100, null=False)
    check_interval_secs = models.PositiveBigIntegerField(null=False)
    last_check_at = models.DateTimeField(null=False, auto_now_add=True)
    next_check_at = models.DateTimeField(null=True)
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PROCESSED,
    )
    max_threads = models.PositiveIntegerField(null=False, default=5)
    count_links_per_page = models.PositiveIntegerField(null=False, default=50)
    max_pages = models.PositiveIntegerField(null=False, default=10)
    batch_size = models.PositiveIntegerField(null=False, default=100)

    def __str__(self):
        return f"HabrHub: {self.pk} {self.name}"


class HabrLinks(models.Model):
    from_hub = models.ForeignKey(HabrHubs, on_delete=models.SET_NULL, null=True)
    from_hub_link = models.CharField(null=False)
    article = models.PositiveBigIntegerField(null=False, unique=True)
    link = models.CharField(max_length=200, null=False)
    title = models.CharField(null=True)
    published_at = models.DateTimeField(null=True)
    author_name = models.CharField(null=True)
    author_link = models.CharField(null=True)
    main_text = models.CharField(null=True)
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PROCESSED,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['article']),
        ]

    def __str__(self):
        return f"HabrLink: {self.pk}, article: {self.article}"
