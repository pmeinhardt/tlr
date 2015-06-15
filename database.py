from peewee import MySQLDatabase, Field, DateTimeField, IntegerField, SQL

class MSQLBinaryField(Field):
    db_field = "binary"

    def __init__(self, length=32, *args, **kwargs):
        super(MSQLBinaryField, self).__init__(*args, **kwargs)
        self.length = length

    def clone_base(self, **kwargs):
        return super(MSQLBinaryField, self).clone_base(
            length=self.length,
            **kwargs
        )

    def get_modifiers(self):
        return self.length and [self.length] or None

class MSQLIntegerField(IntegerField):
    def __init__(self, unsigned=False, zerofill=False, *args, **kwargs):
        super(MSQLIntegerField, self).__init__(*args, **kwargs)
        self.unsigned = unsigned
        self.zerofill = zerofill

    def clone_base(self, **kwargs):
        return super(MSQLIntegerField, self).clone_base(
            unsigned=self.unsigned,
            zerofill=self.zerofill,
            **kwargs
        )

    def __ddl_column__(self, column_type):
        modifiers = self.get_modifiers()
        typedef = column_type
        if modifiers:
            typedef += "(%s)" % (", ".join(map(str, modifiers)))
        if self.unsigned:
            typedef += " UNSIGNED"
        if self.zerofill:
            typedef += " ZEROFILL"
        return SQL(typedef)

class MSQLTinyIntegerField(MSQLIntegerField):
    db_field = "tinyint"

class MSQLSmallIntegerField(MSQLIntegerField):
    db_field = "smallint"

class MSQLMediumIntegerField(MSQLIntegerField):
    db_field = "mediumint"

class MSQLBigIntegerField(MSQLIntegerField):
    db_field = "bigint"

class MSQLTimestampField(DateTimeField):
    db_field = "timestamp"

    def __init__(self, precision=0, *args, **kwargs):
        super(MSQLTimestampField, self).__init__(*args, **kwargs)
        self.precision = precision

    def clone_base(self, **kwargs):
        return super(MSQLTimestampField, self).clone_base(
            precision=self.precision,
            **kwargs
        )

    def get_modifiers(self):
        return self.precision and [self.precision] or None

class MSQLEnumField(Field):
    db_field = "enum"

    def __init__(self, values=[], *args, **kwargs):
        super(MSQLEnumField, self).__init__(*args, **kwargs)
        self.values = values

    def clone_base(self, **kwargs):
        return super(EnumField, self).clone_base(
            values=self.values,
            **kwargs
        )

    def get_modifiers(self):
        return self.values and map(lambda v: "'{0}'".format(v), self.values)

    def db_value(self, value):
        return "'{0}'".format(value)

class MDB(MySQLDatabase): pass

MDB.register_fields({
    "binary": "BINARY",
    "tinyint": "TINYINT",
    "smallint": "SMALLINT",
    "mediumint": "MEDIUMINT",
    "enum": "ENUM",
    "timestamp": "TIMESTAMP",
})
