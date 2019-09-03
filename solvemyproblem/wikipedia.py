from wikipediaapi import Wikipedia as Wiki


class Wikipedia:
    def __init__(self, title):
        self.wiki = Wiki('ru')
        self.title = title

    def page(self):
        page = self.wiki.page(self.title)
        if not page.exists():
            page = self
            setattr(page, 'sections', [])
        return page

    def summary(self):
        page = self.page()
        if page.sections != []:
            return {'Общая информация': page.summary}

    def parse_sections(self, sections, summary=None):
        info = {}

        if summary is not None:
            info.update(summary)

        for section in sections:
            if section.text is '':
                value = self.parse_sections(section.sections)
            else:
                value = section.text
            info[section.title] = value
        return info

    def sections(self):
        return self.parse_sections(self.page().sections, self.summary())
