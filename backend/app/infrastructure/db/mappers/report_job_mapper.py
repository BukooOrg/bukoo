from app.domain.entities.report_job_entity import ReportJobEntity
from app.infrastructure.db.models.report_job_model import ReportJobModel

from .base_mapper import BaseMapper


class ReportJobMapper(BaseMapper[ReportJobModel, ReportJobEntity]):
    @staticmethod
    def to_entity(model: ReportJobModel) -> ReportJobEntity:
        return ReportJobEntity(
            _id=model.id,
            _admin_id=model.admin_id,
            _report_type=model.report_type,
            _date_from=model.date_from,
            _date_to=model.date_to,
            _report_format=model.report_format,
            _status=model.status,
            _limit=model.limit,
            _file_key=model.file_key,
            _error_message=model.error_message,
            _completed_at=model.completed_at,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: ReportJobEntity) -> ReportJobModel:
        model = ReportJobModel(
            admin_id=entity.admin_id,
            report_type=entity.report_type,
            date_from=entity.date_from,
            date_to=entity.date_to,
            report_format=entity.report_format,
            status=entity.status,
        )
        model.id = entity.id
        model.limit = entity.limit
        model.file_key = entity.file_key
        model.error_message = entity.error_message
        model.completed_at = entity.completed_at
        model.deleted_at = entity.deleted_at
        return model
