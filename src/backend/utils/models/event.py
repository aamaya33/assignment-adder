from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EventEntity(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    displayName: Optional[str] = None
    self: Optional[bool] = None


class EventDateTime(BaseModel):
    date: Optional[date] = None
    dateTime: Optional[datetime] = None
    timeZone: Optional[str] = None


class EventAttendee(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    displayName: Optional[str] = None
    organizer: Optional[bool] = None
    self: Optional[bool] = None
    resource: Optional[bool] = None
    optional: Optional[bool] = None
    responseStatus: Optional[str] = None
    comment: Optional[str] = None
    additionalGuests: Optional[int] = None


class ExtendedProperties(BaseModel):
    private: Optional[Dict[str, str]] = None
    shared: Optional[Dict[str, str]] = None


class ConferenceSolutionKey(BaseModel):
    type: Optional[str] = None


class ConferenceSolution(BaseModel):
    key: Optional[ConferenceSolutionKey] = None
    name: Optional[str] = None
    iconUri: Optional[str] = None


class ConferenceCreateStatus(BaseModel):
    statusCode: Optional[str] = None


class ConferenceCreateRequest(BaseModel):
    requestId: Optional[str] = None
    conferenceSolutionKey: Optional[ConferenceSolutionKey] = None
    status: Optional[ConferenceCreateStatus] = None


class ConferenceEntryPoint(BaseModel):
    entryPointType: Optional[str] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    pin: Optional[str] = None
    accessCode: Optional[str] = None
    meetingCode: Optional[str] = None
    passcode: Optional[str] = None
    password: Optional[str] = None


class ConferenceData(BaseModel):
    createRequest: Optional[ConferenceCreateRequest] = None
    entryPoints: Optional[List[ConferenceEntryPoint]] = None
    conferenceSolution: Optional[ConferenceSolution] = None
    conferenceId: Optional[str] = None
    signature: Optional[str] = None
    notes: Optional[str] = None


class GadgetPreferences(BaseModel):
    __root__: Dict[str, str] = Field(default_factory=dict)


class Gadget(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    link: Optional[str] = None
    iconLink: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    display: Optional[str] = None
    preferences: Optional[GadgetPreferences] = None


class ReminderOverride(BaseModel):
    method: Optional[str] = None
    minutes: Optional[int] = None


class Reminders(BaseModel):
    useDefault: Optional[bool] = None
    overrides: Optional[List[ReminderOverride]] = None


class Source(BaseModel):
    url: Optional[str] = None
    title: Optional[str] = None


class CustomLocation(BaseModel):
    label: Optional[str] = None


class OfficeLocation(BaseModel):
    buildingId: Optional[str] = None
    floorId: Optional[str] = None
    floorSectionId: Optional[str] = None
    deskId: Optional[str] = None
    label: Optional[str] = None


class WorkingLocationProperties(BaseModel):
    type: Optional[str] = None
    homeOffice: Optional[Any] = None
    customLocation: Optional[CustomLocation] = None
    officeLocation: Optional[OfficeLocation] = None


class OutOfOfficeProperties(BaseModel):
    autoDeclineMode: Optional[str] = None
    declineMessage: Optional[str] = None


class FocusTimeProperties(BaseModel):
    autoDeclineMode: Optional[str] = None
    declineMessage: Optional[str] = None
    chatStatus: Optional[str] = None


class Attachment(BaseModel):
    fileUrl: Optional[str] = None
    title: Optional[str] = None
    mimeType: Optional[str] = None
    iconLink: Optional[str] = None
    fileId: Optional[str] = None


class BirthdayProperties(BaseModel):
    contact: Optional[str] = None
    type: Optional[str] = None
    customTypeName: Optional[str] = None


class GoogleCalendarEvent(BaseModel):
    kind: Optional[str] = None
    etag: Optional[str] = None
    id: Optional[str] = None
    status: Optional[str] = None
    htmlLink: Optional[str] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    colorId: Optional[str] = None
    creator: Optional[EventEntity] = None
    organizer: Optional[EventEntity] = None
    start: Optional[EventDateTime] = None
    end: Optional[EventDateTime] = None
    endTimeUnspecified: Optional[bool] = None
    recurrence: Optional[List[str]] = None
    recurringEventId: Optional[str] = None
    originalStartTime: Optional[EventDateTime] = None
    transparency: Optional[str] = None
    visibility: Optional[str] = None
    iCalUID: Optional[str] = None
    sequence: Optional[int] = None
    attendees: Optional[List[EventAttendee]] = None
    attendeesOmitted: Optional[bool] = None
    extendedProperties: Optional[ExtendedProperties] = None
    hangoutLink: Optional[str] = None
    conferenceData: Optional[ConferenceData] = None
    gadget: Optional[Gadget] = None
    anyoneCanAddSelf: Optional[bool] = None
    guestsCanInviteOthers: Optional[bool] = None
    guestsCanModify: Optional[bool] = None
    guestsCanSeeOtherGuests: Optional[bool] = None
    privateCopy: Optional[bool] = None
    locked: Optional[bool] = None
    reminders: Optional[Reminders] = None
    source: Optional[Source] = None
    workingLocationProperties: Optional[WorkingLocationProperties] = None
    outOfOfficeProperties: Optional[OutOfOfficeProperties] = None
    focusTimeProperties: Optional[FocusTimeProperties] = None
    attachments: Optional[List[Attachment]] = None
    birthdayProperties: Optional[BirthdayProperties] = None
    eventType: Optional[str] = None

    class Config:
        populate_by_name = True
