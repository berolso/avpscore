

-- SQL update SendStatus table
UPDATE send_status SET has_sent = 'False' WHERE match = 6305;

-- alc delete data from table
  # SendStatus.query.delete()
