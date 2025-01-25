from django.db import models

# Create your models here.
from django.db import models

class UserQuery(models.Model):
    query = models.TextField()  # User's natural language query
    generated_query = models.TextField(null=True, blank=True)  # SQL/NoSQL query
    response = models.TextField(null=True, blank=True)  # Query result
    timestamp = models.DateTimeField(auto_now_add=True)  # When the query was made

    def __str__(self):
        return self.query
