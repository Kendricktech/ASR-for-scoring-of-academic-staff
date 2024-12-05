from django.core.management.base import BaseCommand
from record.models import TextPrompt
import enchant  # PyEnchant library for English word validation

class Command(BaseCommand):
    help = 'Populate the TextPrompt model with valid English words from a given text'

    def handle(self, *args, **kwargs):
        text = """
        xpectancy of accep
        Acceptance letters are not tenable at all levels.
        Scoring of publications and creative works:
        Table 9 Major journal articles and *Books of general interest
        Authors
        So Letter
        Sole
        Up to three More
        Hea Grade
        Author
        authors
        than three Authors
        A
        5.0
        4.0
        3.0
        B
        4.0
        3.0
        2.0
        C
        3.0
        2.0
        1.5
        Dino 2.0
        1.0
        naz 1.0
        To Equp 2.0 o 1.0
        0.5
        Fodo
        0
        0
        noue
        0
        Remarks
        A minimum of 10, 25 and 35 points must be earned from published major journal articles(+) a minimum of 2, 5 and 8 major journal articles must be published in recognized IF- ranked international journals, for promotion to the ranks of Senior Lecturer, Reader and Professor, respectively.
        Subject to a maximum of one of such books per candidate. This item should be bale admissible only for promotion up to the rank of Senior Lecturer.
        nob
        Table 10: Minor journal articles: Minor conference papers (referred); Minor technical report; *Creative works: Musical arrangement, Direction of short opera or concert; Full length performance of one item in a concert, Direction of minor play.
        Authors
        Up to three
        More
        than
        Letter
        Sole
        Grade
        author
        authors
        three authors
        A
        2.0
        1.5
        1.0
        B
        1.5
        1.0
        1.0
        1.0
        1.0
        0.5
        1.0
        0.5
        0.5
        E
        0.5
        0.5
        0.5
        F
        0
        0
        0
        Remarks
        Subject to a maximum of five(5) minor journal articles, three (3) minor conference papers and one(1) minor technical report.
        *Subject to a maximum of 2 of this category of creative works per candidate. Candidate must tender the original letters of commissioning and acceptance (not
        """

        # Initialize the English dictionary
        d = enchant.Dict("en_US")

        # Separate the text into words and deduplicate
        word_list = text.split()
        unique_words = set(word_list)  # Remove duplicates by converting to a set

        # Add valid English words to the TextPrompt model
        added_count = 0
        invalid_words = []  # To store invalid words

        for word in unique_words:
            if d.check(word):  # Check if the word is valid in English
                # Avoid attempting to add duplicates already in the database
                if not TextPrompt.objects.filter(text=word).exists():
                    TextPrompt.objects.create(text=word)
                    added_count += 1
            else:
                invalid_words.append(word)  # Collect invalid words

        # Output success message
        self.stdout.write(self.style.SUCCESS(f"Added {added_count} valid English words to the database!"))
        if invalid_words:
            self.stdout.write(self.style.WARNING(f"Invalid words found (not added): {', '.join(invalid_words)}"))
