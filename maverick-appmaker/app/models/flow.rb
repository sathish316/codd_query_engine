class Flow < ApplicationRecord
  belongs_to :app
  has_many :panels
end
